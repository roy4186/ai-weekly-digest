#!/usr/bin/env python3
"""AIウィークリー：YouTube動画の収集とGeminiによる要点メモ作成。

GitHub Actions から毎日1回実行される想定。
  1. 指定チャンネルの新着動画と、キーワード検索で見つけた動画を集める
  2. 未処理の動画を Gemini に渡し、日本語の要点メモを作る
  3. notes/ にメモ、data/state.json に処理状況、logs/ に実行ログを保存する

外部ライブラリは PyYAML のみ。HTTP 通信は標準ライブラリで行う。
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config.yml"
STATE_PATH = ROOT / "data" / "state.json"
NOTES_DIR = ROOT / "notes"
LOGS_DIR = ROOT / "logs"
INDEX_PATH = NOTES_DIR / "index.json"

JST = dt.timezone(dt.timedelta(hours=9))
YT_API = "https://www.googleapis.com/youtube/v3"
GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta"
UNKNOWN_DURATION_MIN = 15  # RSS など長さが分からない動画の見積もり

try:
    from zoneinfo import ZoneInfo

    PACIFIC = ZoneInfo("America/Los_Angeles")
except Exception:  # pragma: no cover - tzdata が無い環境向け
    PACIFIC = dt.timezone(dt.timedelta(hours=-8))


# ------------------------------------------------------------------
# 共通
# ------------------------------------------------------------------
class HttpError(Exception):
    def __init__(self, status: int, body: str, url: str):
        super().__init__(f"HTTP {status}: {body[:300]}")
        self.status = status
        self.body = body
        self.url = url


class QuotaExhausted(Exception):
    """全モデルで Gemini の上限に達した。"""


class SummarizeError(Exception):
    """この動画は要約できなかった。"""


class ConfigError(Exception):
    """キーやモデル名など設定の問題。動画の失敗回数には数えず、実行を止める。"""


def http_request(method: str, url: str, body: dict | None = None,
                 headers: dict | None = None, timeout: int = 60):
    """JSON（または XML テキスト）を返す。失敗時は HttpError。"""
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("User-Agent", "ai-weekly-digest/1.0")
    if body is not None:
        req.add_header("Content-Type", "application/json")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            ctype = resp.headers.get("Content-Type", "")
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace") if e.fp else ""
        raise HttpError(e.code, raw, url) from None
    except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
        raise HttpError(0, f"{type(e).__name__}: {e}", url) from None
    if "json" in ctype or raw.lstrip().startswith(("{", "[")):
        return json.loads(raw)
    return raw


def now_utc() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def parse_iso(ts: str) -> dt.datetime:
    return dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))


def parse_duration(iso: str | None) -> int | None:
    """PT1H2M3S → 秒。"""
    if not iso:
        return None
    m = re.fullmatch(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso)
    if not m:
        return None
    d, h, mi, s = (int(x) if x else 0 for x in m.groups())
    return d * 86400 + h * 3600 + mi * 60 + s


def fmt_minutes(sec: int | None) -> str:
    return "不明" if sec is None else f"約{max(1, round(sec / 60))}分"


def load_json(path: Path, default):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return default


def save_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")


# ------------------------------------------------------------------
# 実行ログ
# ------------------------------------------------------------------
class RunLog:
    def __init__(self):
        self.started = now_utc()
        self.lines: list[str] = []
        self.warnings: list[str] = []
        self.done: list[str] = []
        self.failed: list[str] = []
        self.skipped: list[str] = []

    def info(self, msg: str):
        print(msg, flush=True)
        self.lines.append(msg)

    def warn(self, msg: str):
        print(f"WARNING: {msg}", flush=True)
        self.warnings.append(msg)

    def write(self, extra: list[str] | None = None) -> None:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        jst = self.started.astimezone(JST)
        path = LOGS_DIR / f"{jst:%Y-%m-%d}.md"
        out = [f"## 実行 {jst:%Y-%m-%d %H:%M} JST", ""]
        out.append(f"- 要約できた: {len(self.done)}本")
        out.append(f"- 失敗（次回再挑戦）: {len(self.failed)}本")
        out.append(f"- 諦めた: {len(self.skipped)}本")
        for title, items in (("要約できた動画", self.done),
                             ("失敗した動画", self.failed),
                             ("諦めた動画", self.skipped),
                             ("注意", self.warnings)):
            if items:
                out += ["", f"### {title}"] + [f"- {x}" for x in items]
        if extra:
            out += [""] + extra
        if self.lines:
            out += ["", "<details><summary>詳細ログ</summary>", "", "```"]
            out += [re.sub(r"AIza[0-9A-Za-z_\-]{10,}", "[KEY]", l) for l in self.lines]
            out += ["```", "", "</details>"]
        out.append("")
        prev = path.read_text(encoding="utf-8") if path.exists() else f"# {jst:%Y-%m-%d} の実行ログ\n\n"
        path.write_text(prev + "\n".join(out) + "\n", encoding="utf-8")


# ------------------------------------------------------------------
# YouTube
# ------------------------------------------------------------------
class YouTube:
    def __init__(self, api_key: str | None, log: RunLog):
        self.key = api_key
        self.log = log
        self.api_ok = bool(api_key)

    def _get(self, path: str, params: dict):
        params = dict(params, key=self.key)
        url = f"{YT_API}/{path}?{urllib.parse.urlencode(params)}"
        return http_request("GET", url, timeout=30)

    def resolve_channel_id(self, handle: str) -> str | None:
        if not self.api_ok or not handle:
            return None
        data = self._get("channels", {"part": "id", "forHandle": handle})
        items = data.get("items") or []
        return items[0]["id"] if items else None

    def recent_uploads(self, channel_id: str, since: dt.datetime) -> list[str]:
        """チャンネルの新着動画 ID（API 優先、失敗時は RSS）。"""
        if self.api_ok:
            try:
                playlist = "UU" + channel_id[2:]
                data = self._get("playlistItems", {
                    "part": "contentDetails", "playlistId": playlist,
                    "maxResults": 25})
                ids = []
                for it in data.get("items", []):
                    cd = it.get("contentDetails", {})
                    pub = cd.get("videoPublishedAt")
                    if pub and parse_iso(pub) >= since:
                        ids.append(cd["videoId"])
                return ids
            except HttpError as e:
                self.log.warn(f"YouTube API でチャンネル {channel_id} の取得に失敗（RSSで代替）: {e}")
                if e.status in (400, 403):
                    self.api_ok = False  # キー不正・上限超過。以降は RSS のみ
        return [v["id"] for v in self.rss_uploads(channel_id) if v["published"] >= since]

    def rss_uploads(self, channel_id: str) -> list[dict]:
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        try:
            raw = http_request("GET", url, timeout=30)
        except HttpError as e:
            self.log.warn(f"RSS でもチャンネル {channel_id} を取得できませんでした: {e}")
            return []
        ns = {"a": "http://www.w3.org/2005/Atom",
              "yt": "http://www.youtube.com/xml/schemas/2015",
              "media": "http://search.yahoo.com/mrss/"}
        out = []
        try:
            root = ET.fromstring(raw)
        except ET.ParseError:
            self.log.warn(f"RSS の解析に失敗: {channel_id}")
            return []
        for e in root.findall("a:entry", ns):
            vid = e.findtext("yt:videoId", default="", namespaces=ns)
            pub = e.findtext("a:published", default="", namespaces=ns)
            if not (vid and pub):
                continue
            link = e.find("a:link", ns)
            href = link.get("href", "") if link is not None else ""
            stats = e.find("media:group/media:community/media:statistics", ns)
            views = int(stats.get("views", "0") or 0) if stats is not None else None
            out.append({"id": vid, "published": parse_iso(pub),
                        "title": e.findtext("a:title", default="", namespaces=ns),
                        "channel": e.findtext("a:author/a:name", default="", namespaces=ns),
                        "is_short": "/shorts/" in href, "views": views})
        return out

    def details(self, ids: list[str]) -> dict[str, dict]:
        """動画の詳細。API が使えないときは RSS 由来の最小情報を返せないので空。"""
        out: dict[str, dict] = {}
        if not self.api_ok:
            return out
        for i in range(0, len(ids), 50):
            chunk = ids[i:i + 50]
            try:
                data = self._get("videos", {
                    "part": "snippet,contentDetails,statistics",
                    "id": ",".join(chunk), "maxResults": 50})
            except HttpError as e:
                self.log.warn(f"動画情報の取得に失敗: {e}")
                if e.status in (400, 403):
                    self.api_ok = False
                return out
            for it in data.get("items", []):
                sn = it.get("snippet", {})
                out[it["id"]] = {
                    "id": it["id"],
                    "title": sn.get("title", ""),
                    "channel": sn.get("channelTitle", ""),
                    "channel_id": sn.get("channelId", ""),
                    "published": sn.get("publishedAt", ""),
                    "live": sn.get("liveBroadcastContent", "none"),
                    "duration_sec": parse_duration(it.get("contentDetails", {}).get("duration")),
                    "views": int(it.get("statistics", {}).get("viewCount", 0) or 0),
                }
        return out

    def search(self, q: str, lang: str | None, since: dt.datetime) -> list[str]:
        if not self.api_ok:
            return []
        params = {"part": "id", "type": "video", "order": "viewCount", "q": q,
                  "publishedAfter": since.strftime("%Y-%m-%dT%H:%M:%SZ"),
                  "maxResults": 15}
        if lang:
            params["relevanceLanguage"] = lang
        try:
            data = self._get("search", params)
        except HttpError as e:
            self.log.warn(f"検索「{q}」に失敗: {e}")
            if e.status in (400, 403):
                self.api_ok = False
            return []
        return [it["id"]["videoId"] for it in data.get("items", [])
                if it.get("id", {}).get("videoId")]


# ------------------------------------------------------------------
# Gemini
# ------------------------------------------------------------------
PROMPT = """あなたはAI業界の動画を視聴して要点メモを作る記者です。
以下のYouTube動画を最初から最後まで確認し、{language}でメモを書いてください。

動画情報:
- タイトル: {title}
- チャンネル: {channel}
- 公開日: {published}
- 長さ: {duration}

ルール:
- 動画の中で実際に話された・映った内容だけを書く。推測や動画外の知識で補わない。
- 製品名・機能名・数字・日付は動画内の表記どおりに書く。
- タイムスタンプは MM:SS（1時間以上は H:MM:SS）で書く。
- 宣伝・雑談・スポンサー紹介は省く。

次の見出しで、Markdownだけを出力してください（前置きや締めの挨拶は不要）:

## 3行要約
## 主な内容
（タイムスタンプ付きの箇条書きで5〜10個）
## 発表・新機能・数字
（該当がなければ「特になし」）
## 関係する会社・製品
（Anthropic / OpenAI / Google / その他 のうち該当するものと製品名）
## 誰に役立つか
## おすすめ度
（「★★★★☆」のように★を5つ並べた形式で評価し、その理由を1行）
## 見どころ
（特に見る価値のある箇所を、タイムスタンプ付きで2〜3個）
"""


class Gemini:
    VARIANTS = ("interactions_full", "interactions_min", "generate_min")
    AUDIO_TOK_PER_SEC = 32   # 低解像度時の目安（公式ドキュメント）
    FRAME_TOK = 66           # 低解像度の1フレームあたり

    def __init__(self, api_key: str, cfg: dict, state: dict, log: RunLog):
        self.key = api_key
        self.models = list(cfg.get("models") or ["gemini-3.8-flash"])
        self.language = cfg.get("language", "日本語")
        self.tpm_limit = int(cfg.get("tokens_per_request_limit", 230000))
        self.min_interval = float(cfg.get("min_interval_sec", 13))
        self.timeout = int(cfg.get("request_timeout_sec", 600))
        self.state = state
        self.log = log
        self.dead_models: set[str] = set()   # 404 等で使えないモデル
        self.quota_models: set[str] = set()  # 今回の実行で1日の上限に達したモデル
        self._last_call = 0.0
        self._last_tokens = 0

    # --- 見積もりと間隔調整 --------------------------------------------
    def plan_fps(self, dur: int | None) -> float:
        """1回のリクエストが1分あたりの上限に収まるようにフレーム間隔を決める。"""
        if not dur:
            return 1.0
        fps = (self.tpm_limit / dur - self.AUDIO_TOK_PER_SEC) / self.FRAME_TOK
        return max(0.05, min(1.0, round(fps, 2)))

    def estimate_tokens(self, dur: int | None, fps: float = 1.0) -> int:
        if not dur:
            return 60000
        return int(dur * (self.AUDIO_TOK_PER_SEC + self.FRAME_TOK * fps))

    def fits(self, dur: int | None) -> bool:
        return self.estimate_tokens(dur, 0.05) <= self.tpm_limit

    def _pace(self, est_tokens: int):
        """無料枠の「1分あたり」の上限に当たらないよう、リクエストの間隔をあける。"""
        wait = self.min_interval
        if self._last_tokens > self.tpm_limit * 0.4:
            wait = max(wait, 62)  # 大きい動画の直後は1分あける
        if est_tokens + self._last_tokens > self.tpm_limit:
            wait = max(wait, 62)
        remaining = wait - (time.time() - self._last_call)
        if remaining > 0:
            time.sleep(remaining)

    # --- リクエスト本体 -------------------------------------------------
    def _headers(self):
        return {"x-goog-api-key": self.key}

    def _interactions(self, model: str, url: str, prompt: str, fps: float, full: bool) -> str:
        video = {"type": "video", "uri": url, "resolution": "low"}
        body: dict = {"model": model, "input": [{"type": "text", "text": prompt}, video]}
        if full:
            if fps < 1.0:
                video["processing"] = {"type": "static", "fps": fps}
            body["generation_config"] = {"max_output_tokens": 8192, "thinking_level": "low"}
        data = http_request("POST", f"{GEMINI_BASE}/interactions", body,
                            self._headers(), timeout=self.timeout)
        status = data.get("status")
        if status not in (None, "completed", "incomplete"):
            raise HttpError(503, f"interaction status={status}", url)
        texts = []
        for step in data.get("steps") or []:
            if step.get("type") == "model_output":
                for c in step.get("content") or []:
                    if c.get("type") == "text" and c.get("text"):
                        texts.append(c["text"])
        return "\n".join(texts).strip() or (data.get("output_text") or "").strip()

    def _generate(self, model: str, url: str, prompt: str, fps: float) -> str:
        part = {"file_data": {"file_uri": url}}
        if fps < 1.0:
            part["video_metadata"] = {"fps": fps}
        body = {
            "contents": [{"role": "user", "parts": [part, {"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": 8192,
                                 "mediaResolution": "MEDIA_RESOLUTION_LOW"},
        }
        data = http_request("POST", f"{GEMINI_BASE}/models/{model}:generateContent",
                            body, self._headers(), timeout=self.timeout)
        cands = data.get("candidates") or []
        if not cands:
            return ""
        parts = cands[0].get("content", {}).get("parts") or []
        return "\n".join(p["text"] for p in parts
                         if p.get("text") and not p.get("thought")).strip()

    def _call(self, variant: str, model: str, url: str, prompt: str, fps: float) -> str:
        if variant == "interactions_full":
            return self._interactions(model, url, prompt, fps, full=True)
        if variant == "interactions_min":
            return self._interactions(model, url, prompt, fps, full=False)
        return self._generate(model, url, prompt, fps)

    # --- 切り替えロジック ----------------------------------------------
    def _ordered_variants(self, model: str) -> list[str]:
        hint = self.state.get("api_hint", {}).get(model)
        order = list(self.VARIANTS)
        if hint in order:
            order.remove(hint)
            order.insert(0, hint)
        return order

    @staticmethod
    def _short(e: Exception) -> str:
        body = getattr(e, "body", str(e))
        m = re.search(r'"message"\s*:\s*"([^"]{0,160})', body)
        return (m.group(1) if m else body.replace("\n", " "))[:160]

    def _try(self, variant: str, model: str, url: str, prompt: str, fps: float, est: int):
        """1つの書き方で試す。戻り値: (text or None, error, 次の行動)。

        次の行動: "next_variant"（別の書き方へ）/ "next_model"（別モデルへ）
        """
        for attempt in (1, 2):
            self._pace(est)
            t0 = time.time()
            try:
                text = self._call(variant, model, url, prompt, fps)
            except HttpError as e:
                el = time.time() - t0
                self._last_call, self._last_tokens = time.time(), est
                self.log.info(f"    · {model} [{variant}] → HTTP {e.status}（{el:.0f}秒）{self._short(e)}")
                if e.status == 429:
                    if re.search(r"per ?day|PerDay", e.body, re.IGNORECASE):
                        self.quota_models.add(model)
                        self.log.warn(f"{model} は本日の上限に達しました")
                        return None, e, "next_model"
                    if attempt == 1:
                        time.sleep(65)  # 1分あたりの上限 → 1分待って再試行
                        continue
                    return None, e, "next_model"
                if e.status == 404:
                    self.dead_models.add(model)
                    self.log.warn(f"{model} が見つかりません（404）。次のモデルへ")
                    return None, e, "next_model"
                if e.status == 401 or (e.status == 403 and "api key" in e.body.lower().replace("_", " ")):
                    raise ConfigError(f"Gemini の APIキーが無効か権限がありません: {self._short(e)}") from None
                if e.status in (400, 403, 422):
                    return None, e, "next_variant"  # 書き方か動画側の問題
                if e.status == 0:
                    return None, e, "next_model"    # 時間切れ・通信エラーは同じ条件で繰り返さない
                if attempt == 1:
                    time.sleep(45)  # 一時的な不調（5xx・混雑）は少し待って1回だけ再試行
                    continue
                return None, e, "next_model"
            el = time.time() - t0
            self._last_call, self._last_tokens = time.time(), est
            if text and len(text) > 80:
                self.log.info(f"    · {model} [{variant}] → OK（{el:.0f}秒・{len(text)}字）")
                return text, None, ""
            self.log.info(f"    · {model} [{variant}] → 応答が空か短すぎます（{el:.0f}秒）")
            return None, SummarizeError("応答が空か短すぎます"), "next_variant"
        return None, SummarizeError("不明なエラー"), "next_model"

    def summarize(self, video: dict, attempts: int = 0) -> tuple[str, str]:
        url = f"https://www.youtube.com/watch?v={video['id']}"
        dur = video.get("duration_sec")
        # 前回失敗した動画は、フレームをさらに間引いて軽くしてから再挑戦する
        fps = max(0.05, round(self.plan_fps(dur) / (1 + attempts), 2))
        est = self.estimate_tokens(dur, fps)
        pub = video.get("published", "")
        try:
            pub = parse_iso(pub).astimezone(JST).strftime("%Y-%m-%d")
        except Exception:
            pass
        prompt = PROMPT.format(language=self.language, title=video.get("title", ""),
                               channel=video.get("channel", ""), published=pub,
                               duration=fmt_minutes(dur))
        last_err: Exception | None = None
        for model in self.models:
            if model in self.dead_models or model in self.quota_models:
                continue
            only_bad_request = True
            moved_on = False
            for variant in self._ordered_variants(model):
                text, err, action = self._try(variant, model, url, prompt, fps, est)
                if text:
                    self.state.setdefault("api_hint", {})[model] = variant
                    return text, model
                last_err = err
                if not (isinstance(err, HttpError) and err.status in (400, 403, 422)):
                    only_bad_request = False
                if action == "next_model":
                    moved_on = True
                    break
            if not moved_on and only_bad_request:
                # どの書き方でも 400 系 → 動画側（非公開・地域制限など）の可能性が高い
                raise SummarizeError(f"動画を処理できません: {self._short(last_err)}")
        unusable = self.dead_models | self.quota_models
        if self.models and all(m in unusable for m in self.models):
            if self.quota_models:
                raise QuotaExhausted(str(last_err))
            raise ConfigError("config.yml の gemini.models に使えるモデルがありません（モデル名を確認）")
        raise SummarizeError(self._short(last_err) if last_err else "不明なエラー")


# ------------------------------------------------------------------
# メモの保存
# ------------------------------------------------------------------
def write_note(video: dict, text: str, model: str) -> Path:
    try:
        pub = parse_iso(video["published"]).astimezone(JST)
    except Exception:
        pub = now_utc().astimezone(JST)
    NOTES_DIR.mkdir(parents=True, exist_ok=True)
    path = NOTES_DIR / f"{pub:%Y-%m-%d}_{video['id']}.md"
    meta = {
        "video_id": video["id"],
        "title": video.get("title", ""),
        "channel": video.get("channel", ""),
        "company": video.get("company", ""),
        "url": f"https://www.youtube.com/watch?v={video['id']}",
        "published": pub.strftime("%Y-%m-%d %H:%M JST"),
        "duration_min": round(video["duration_sec"] / 60) if video.get("duration_sec") else None,
        "views": video.get("views"),
        "source": video.get("source", "channel"),
        "query": video.get("query", ""),
        "model": model,
        "processed_at": now_utc().astimezone(JST).strftime("%Y-%m-%d %H:%M JST"),
    }
    front = "\n".join(f"{k}: {json.dumps(v, ensure_ascii=False)}" for k, v in meta.items())
    path.write_text(f"---\n{front}\n---\n\n# {video.get('title', '')}\n\n{text.strip()}\n",
                    encoding="utf-8")
    return path


def stars(text: str) -> int | None:
    sec = text.split("おすすめ度", 1)[1][:120] if "おすすめ度" in text else ""
    m = re.search(r"★\s*([1-5])(?![0-9])", sec) or re.search(r"([1-5])\s*(?:/\s*5|点)", sec)
    if m:
        return int(m.group(1))
    m = re.search(r"(★+)", sec)
    return len(m.group(1)) if m else None


def title_matches(title: str, keywords: list[str]) -> bool:
    """英単語は単語単位で照合（"AI" が "maintain" に当たらないように）。"""
    for k in keywords:
        if re.search(rf"(?<![A-Za-z]){re.escape(k)}(?![A-Za-z])", title, re.IGNORECASE):
            return True
    return False


def update_index(state: dict) -> None:
    """notes/index.json：週次まとめ用の一覧（直近120日）。"""
    cutoff = now_utc() - dt.timedelta(days=120)
    rows = []
    for vid, s in state.get("videos", {}).items():
        if s.get("status") != "done":
            continue
        try:
            if parse_iso(s["updated"]) < cutoff:
                continue
        except Exception:
            pass
        note = ROOT / s.get("note", "")
        if s.get("note") and note.exists():
            s["stars"] = stars(note.read_text(encoding="utf-8"))
        rows.append({k: s.get(k) for k in (
            "title", "channel", "company", "published", "source", "query",
            "duration_min", "views", "stars", "note", "updated")} | {"video_id": vid})
    rows.sort(key=lambda r: r.get("published") or "", reverse=True)
    save_json(INDEX_PATH, rows)


# ------------------------------------------------------------------
# メイン
# ------------------------------------------------------------------
def pacific_today() -> str:
    return now_utc().astimezone(PACIFIC).strftime("%Y-%m-%d")


def main() -> int:
    log = RunLog()
    cfg = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
    state = load_json(STATE_PATH, {})
    state.setdefault("videos", {})

    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    yt_key = os.environ.get("YOUTUBE_API_KEY", "").strip()
    if not gemini_key:
        log.warn("GEMINI_API_KEY が設定されていません。GitHub の Settings → Secrets を確認してください。")
        log.write()
        return 1
    if not yt_key:
        log.warn("YOUTUBE_API_KEY が未設定のため、RSSのみで新着を確認します（発掘枠は停止）。")

    filters = cfg.get("filters", {})
    gcfg = cfg.get("gemini", {})
    dcfg = cfg.get("discovery", {})
    since = now_utc() - dt.timedelta(days=int(filters.get("lookback_days", 8)))
    min_sec = int(filters.get("min_duration_sec", 180))
    max_sec = int(filters.get("max_duration_min", 240)) * 60
    max_attempts = int(gcfg.get("max_attempts", 3))

    yt = YouTube(yt_key or None, log)
    videos = state["videos"]

    def finished(vid: str) -> bool:
        s = videos.get(vid, {})
        return s.get("status") in ("done", "skipped", "too_long")

    # ---- 1. 指定チャンネル -------------------------------------------
    channel_ids: dict[str, dict] = {}
    channel_candidates: list[dict] = []
    for ch in cfg.get("channels") or []:
        cid = (ch.get("channel_id") or "").strip()
        if not cid:
            try:
                cid = yt.resolve_channel_id(ch.get("handle", "")) or ""
            except HttpError as e:
                log.warn(f"{ch.get('name')} のチャンネルIDを特定できません: {e}")
        if not cid:
            log.warn(f"{ch.get('name')}（{ch.get('handle')}）のチャンネルIDが不明のためスキップ")
            continue
        channel_ids[cid] = ch
        ids = [v for v in yt.recent_uploads(cid, since) if not finished(v)]
        if not ids:
            continue
        info = yt.details(ids)
        rss_meta = {}
        if not info:  # API なし → RSS の情報で代用
            rss_meta = {v["id"]: v for v in yt.rss_uploads(cid)}
        keywords = [str(k) for k in ch.get("include_keywords") or []]
        for vid in ids:
            v = info.get(vid)
            if v is None:
                r = rss_meta.get(vid)
                # RSS では長さが分からないため、ショートと再生0（配信予定の可能性）は見送る
                if not r or r["is_short"] or r["views"] == 0:
                    continue
                v = {"id": vid, "title": r["title"], "channel": r["channel"] or ch.get("name"),
                     "channel_id": cid, "published": r["published"].isoformat(),
                     "live": "none", "duration_sec": None, "views": r["views"]}
            if v["live"] in ("live", "upcoming"):
                continue
            d = v.get("duration_sec")
            if d is not None and (d < min_sec or d > max_sec):
                continue
            if keywords and not title_matches(v["title"], keywords):
                continue
            v.update(source="channel", company=ch.get("company", ""))
            channel_candidates.append(v)
    channel_candidates.sort(key=lambda v: v.get("published") or "")

    # ---- 2. 発掘枠 --------------------------------------------------
    discovery_candidates: list[dict] = []
    if dcfg.get("enabled", True) and yt.api_ok:
        found: dict[str, str] = {}
        for q in dcfg.get("queries") or []:
            if isinstance(q, str):
                q = {"q": q}
            for vid in yt.search(q["q"], q.get("lang"), since):
                found.setdefault(vid, q["q"])
        excluded = set(dcfg.get("exclude_channels") or []) | set(channel_ids)
        ids = [v for v in found if not finished(v)]
        info = yt.details(ids)
        min_views = int(dcfg.get("min_views", 5000))
        for vid, v in info.items():
            d = v.get("duration_sec")
            if v["live"] in ("live", "upcoming") or v["channel_id"] in excluded:
                continue
            if d is None or d < min_sec or d > max_sec or v["views"] < min_views:
                continue
            v.update(source="discovery", query=found[vid], company="")
            discovery_candidates.append(v)
        discovery_candidates.sort(key=lambda v: v["views"], reverse=True)
        discovery_candidates = discovery_candidates[: int(dcfg.get("per_run", 2))]

    # 発掘枠が毎回後回しにならないよう、1回の上限のうち発掘分の枠を先に確保する
    cap_total = int(gcfg.get("max_videos_per_run", 8))
    head = max(0, cap_total - len(discovery_candidates))
    queue = channel_candidates[:head] + discovery_candidates + channel_candidates[head:]
    log.info(f"候補: 指定チャンネル {len(channel_candidates)}本 / 発掘 {len(discovery_candidates)}本")

    # ---- 3. Gemini で要約 -------------------------------------------
    usage = state.get("usage", {})
    if usage.get("date_pt") != pacific_today():
        usage = {"date_pt": pacific_today(), "minutes": 0}
    budget = int(gcfg.get("daily_minutes_budget", 420))
    cap = int(gcfg.get("max_videos_per_run", 8))
    gem = Gemini(gemini_key, gcfg, state, log)
    run_deadline = time.time() + int(gcfg.get("max_run_minutes", 50)) * 60
    attempted = 0
    hard_errors = 0
    quota_hit = False
    config_error = False

    for v in queue:
        if attempted >= cap:
            log.info(f"1回あたりの上限（{cap}本）に達したため、残りは次回に回します")
            break
        if time.time() > run_deadline:
            log.info("1回あたりの実行時間の上限に達したため、残りは次回に回します")
            break
        vid = v["id"]
        label = f"{v.get('title', vid)}（{v.get('channel', '')}）"
        if not gem.fits(v.get("duration_sec")):
            videos[vid] = {"status": "too_long", "title": v.get("title", ""),
                           "duration_min": round(v["duration_sec"] / 60),
                           "updated": now_utc().isoformat()}
            log.skipped.append(f"{label} — 長すぎるため見送り（無料枠の1回あたりの上限を超える）")
            log.info(f"長すぎるため見送り: {label}")
            save_json(STATE_PATH, state)
            continue
        minutes = (v["duration_sec"] / 60) if v.get("duration_sec") else UNKNOWN_DURATION_MIN
        if usage["minutes"] + minutes > budget:
            log.info(f"本日の処理時間の上限（{budget}分）を超えるため次回に回します: {v.get('title', v['id'])}")
            continue  # 短い動画なら入るかもしれないので次へ
        rec = videos.setdefault(vid, {"attempts": 0})
        attempted += 1
        log.info(f"▶ [{attempted}] {label}｜{fmt_minutes(v.get('duration_sec'))}｜"
                 f"見積もり約{gem.estimate_tokens(v.get('duration_sec'), gem.plan_fps(v.get('duration_sec'))) // 1000}Kトークン")
        try:
            text, model = gem.summarize(v, rec.get("attempts", 0))
        except QuotaExhausted:
            attempted -= 1
            quota_hit = True
            if "status" not in rec:
                videos.pop(vid, None)
            log.warn("Gemini の無料枠の上限に達したため、今回はここまでにします（次回自動で再開）")
            break
        except ConfigError as e:
            attempted -= 1
            config_error = True
            if "status" not in rec:
                videos.pop(vid, None)
            log.warn(str(e))
            break
        except SummarizeError as e:
            rec["attempts"] = rec.get("attempts", 0) + 1
            rec.update(title=v.get("title", ""), last_error=str(e)[:500],
                       updated=now_utc().isoformat())
            if rec["attempts"] >= max_attempts:
                rec["status"] = "skipped"
                log.skipped.append(f"{label} — {str(e)[:150]}")
            else:
                rec["status"] = "failed"
                log.failed.append(f"{label} — {str(e)[:150]}")
            hard_errors += 1
            log.info(f"  ✗ 失敗: {str(e)[:150]}")
            save_json(STATE_PATH, state)
            continue
        usage["minutes"] += minutes
        note = write_note(v, text, model)
        rec.update(status="done", title=v.get("title", ""), channel=v.get("channel", ""),
                   company=v.get("company", ""), source=v.get("source", ""),
                   query=v.get("query", ""), views=v.get("views"),
                   duration_min=round(v["duration_sec"] / 60) if v.get("duration_sec") else None,
                   published=v.get("published", ""), stars=stars(text),
                   note=str(note.relative_to(ROOT)), model=model,
                   updated=now_utc().isoformat())
        rec.pop("last_error", None)
        log.done.append(f"{label} → {note.name}")
        log.info(f"  ✓ メモ作成: {note.name}")
        state["usage"] = usage
        save_json(STATE_PATH, state)

    state["usage"] = usage
    state["last_run"] = now_utc().isoformat()
    save_json(STATE_PATH, state)
    update_index(state)
    extra = [f"本日（米国太平洋時間 {usage['date_pt']}）の処理済み動画: 約{round(usage['minutes'])}分"]
    if quota_hit:
        extra.append("Geminiの上限に達したため途中で終了しました。")
    log.write(extra)

    if config_error:
        return 1  # 設定の問題 → GitHub から失敗メールが届くように
    if attempted and not log.done and hard_errors and not quota_hit:
        return 1  # 全滅 → 同上
    if cfg.get("channels") and not channel_ids:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
