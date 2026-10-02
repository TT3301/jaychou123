# -*- coding: utf-8 -*-
# 豆瓣导航搜索版 - 仅分类/推荐/搜索，不做播放解析
# 结构参考直播大全 Spider
import json
import re
import sys
import time
from urllib.parse import quote, urlencode

sys.path.append('..')
from base.spider import Spider


class Spider(Spider):

    def init(self, extend=""):
        self.host = "https://frodo.douban.com/api/v2"
        self.apikey = "0ac44ae016490db2204ce0a042db2916"
        self.ua = "api-client/1 com.douban.frodo/7.22.0.beta9(231) Android/23 product/Mate 40 vendor/HUAWEI model/Mate 40 brand/HUAWEI  rom/android  network/wifi  platform/AndroidPad"
        self.headers = {
            "User-Agent": self.ua,
            "Referer": "https://servicewechat.com/wx2f9b06c1de1ccfca/91/page-frame.html",
        }
        return self

    def getName(self):
        return "豆瓣导航"

    def isVideoFormat(self, url):
        return False

    def manualVideoCheck(self):
        return False

    def destroy(self):
        pass

    # ---------- 分类（导航） ----------
    def homeContent(self, filter):
        classes = [
            {"type_id": "movie_hot", "type_name": "电影热门"},
            {"type_id": "tv_hot", "type_name": "剧集热门"},
            {"type_id": "tv_variety", "type_name": "综艺热门"},
            {"type_id": "rank_movie", "type_name": "电影榜单"},
            {"type_id": "rank_tv", "type_name": "剧集榜单"},
            {"type_id": "rank_show", "type_name": "综艺榜单"},
            {"type_id": "movie_coming", "type_name": "即将上映"},
            {"type_id": "tv_chinese", "type_name": "国产剧"},
            {"type_id": "tv_american", "type_name": "美剧"},
            {"type_id": "tv_korean", "type_name": "韩剧"},
            {"type_id": "tv_japanese", "type_name": "日剧"},
            {"type_id": "movie_top250", "type_name": "Top250"},
        ]
        filters = {
            "movie_hot": [{
                "key": "sort",
                "name": "排序",
                "value": [
                    {"n": "热度", "v": ""},
                    {"n": "评分", "v": "R"},
                    {"n": "时间", "v": "T"},
                ],
            }],
            "tv_hot": [{
                "key": "sort",
                "name": "排序",
                "value": [
                    {"n": "热度", "v": ""},
                    {"n": "评分", "v": "R"},
                    {"n": "时间", "v": "T"},
                ],
            }],
        }
        return {"class": classes, "filters": filters}

    def homeVideoContent(self):
        # 首页推荐：电影热门前 20
        try:
            items = self._subject_collection("movie_hot_gaia", 0, 20)
            return {"list": [self._to_vod(x) for x in items if x]}
        except Exception:
            return {"list": []}

    # ---------- 分类列表 ----------
    def categoryContent(self, tid, pg, filter, extend):
        pg = int(pg or 1)
        start = (pg - 1) * 20
        sort = (extend or {}).get("sort", "")
        items = []
        try:
            if tid == "movie_hot":
                items = self._subject_collection("movie_hot_gaia", start, 20, sort)
            elif tid == "tv_hot":
                items = self._subject_collection("tv_hot", start, 20, sort)
            elif tid == "tv_variety":
                items = self._subject_collection("show_hot", start, 20, sort)
            elif tid == "rank_movie":
                items = self._subject_collection("movie_showing", start, 20)
            elif tid == "rank_tv":
                items = self._subject_collection("tv_domestic", start, 20)
            elif tid == "rank_show":
                items = self._subject_collection("show_domestic", start, 20)
            elif tid == "movie_coming":
                items = self._subject_collection("movie_soon", start, 20)
            elif tid == "tv_chinese":
                items = self._subject_collection("tv_chinese", start, 20)
            elif tid == "tv_american":
                items = self._subject_collection("tv_american", start, 20)
            elif tid == "tv_korean":
                items = self._subject_collection("tv_korean", start, 20)
            elif tid == "tv_japanese":
                items = self._subject_collection("tv_japanese", start, 20)
            elif tid == "movie_top250":
                items = self._subject_collection("movie_top250", start, 20)
            else:
                items = self._subject_collection("movie_hot_gaia", start, 20)
        except Exception as e:
            print("category error:", e)
            items = []

        vods = [self._to_vod(x) for x in items if x]
        return {
            "list": vods,
            "page": pg,
            "pagecount": 50,
            "limit": 20,
            "total": 1000,
        }

    # ---------- 详情：仅展示信息，无播放线路（导航用） ----------
    def detailContent(self, ids):
        vid = ids[0] if isinstance(ids, list) else ids
        try:
            data = self._get(f"/subject/{vid}", {"apikey": self.apikey})
            if not data:
                return {"list": []}
            title = data.get("title") or data.get("name") or ""
            pic = (data.get("pic") or {}).get("normal") or (data.get("pic") or {}).get("large") or ""
            year = str((data.get("year") or "")[:4])
            rating = data.get("rating") or {}
            score = rating.get("value") or ""
            genres = "/".join(data.get("genres") or [])
            countries = "/".join(data.get("countries") or [])
            directors = "/".join([x.get("name", "") for x in (data.get("directors") or [])[:5]])
            actors = "/".join([x.get("name", "") for x in (data.get("actors") or [])[:8]])
            intro = data.get("intro") or data.get("card_subtitle") or ""
            remarks = f"{score}分" if score else ""
            content = f"{year} · {genres}\n{countries}\n导演: {directors}\n主演: {actors}\n\n{intro}"
            # 无播放源：导航搜索专用
            vod = {
                "vod_id": str(vid),
                "vod_name": title,
                "vod_pic": pic,
                "vod_year": year,
                "vod_remarks": remarks,
                "vod_content": content,
                "vod_actor": actors,
                "vod_director": directors,
                "type_name": genres,
                "vod_area": countries,
                "vod_play_from": "豆瓣导航",
                "vod_play_url": "请用其他源搜索同名影片播放$https://www.douban.com",
            }
            return {"list": [vod]}
        except Exception as e:
            print("detail error:", e)
            return {"list": []}

    # ---------- 搜索 ----------
    def searchContent(self, key, quick, pg="1"):
        pg = int(pg or 1)
        start = (pg - 1) * 20
        try:
            data = self._get(
                "/search/subjects",
                {
                    "apikey": self.apikey,
                    "q": key,
                    "count": 20,
                    "start": start,
                },
            )
            items = (data or {}).get("items") or (data or {}).get("subjects") or []
            # frodo 搜索结构可能是 items[].target
            vods = []
            for it in items:
                target = it.get("target") if isinstance(it, dict) and "target" in it else it
                if not target:
                    continue
                v = self._to_vod(target)
                if v:
                    vods.append(v)
            return {"list": vods, "page": pg, "pagecount": 20, "limit": 20, "total": 400}
        except Exception as e:
            print("search error:", e)
            return {"list": []}

    def playerContent(self, flag, id, vipFlags):
        # 导航源不提供真实播放
        return {"parse": 0, "url": "", "header": {}}

    # ---------- 内部请求 ----------
    def _get(self, path, params=None):
        params = dict(params or {})
        if "apikey" not in params:
            params["apikey"] = self.apikey
        url = self.host + path
        try:
            r = self.fetch(url, params=params, headers=self.headers, timeout=12)
            if hasattr(r, "json"):
                return r.json()
            return json.loads(r.content.decode("utf-8", errors="ignore"))
        except Exception as e:
            print("request fail", path, e)
            return {}

    def _subject_collection(self, collection_id, start=0, count=20, sort=""):
        params = {
            "apikey": self.apikey,
            "start": start,
            "count": count,
            "items_only": 1,
            "for_mobile": 1,
        }
        if sort:
            params["sort"] = sort
        data = self._get(f"/subject_collection/{collection_id}/items", params)
        items = (data or {}).get("subject_collection_items") or (data or {}).get("items") or []
        return items

    def _to_vod(self, item):
        if not isinstance(item, dict):
            return None
        # 兼容不同字段
        vid = item.get("id") or item.get("target_id") or ""
        if not vid:
            return None
        title = item.get("title") or item.get("name") or ""
        pic_obj = item.get("pic") or item.get("cover") or {}
        if isinstance(pic_obj, dict):
            pic = pic_obj.get("normal") or pic_obj.get("large") or pic_obj.get("url") or ""
        else:
            pic = str(pic_obj or "")
        rating = item.get("rating") or {}
        score = rating.get("value") if isinstance(rating, dict) else ""
        year = str(item.get("year") or "")[:4]
        card = item.get("card_subtitle") or item.get("subtitle") or ""
        remarks = f"{score}分" if score else (card or year)
        return {
            "vod_id": str(vid),
            "vod_name": title,
            "vod_pic": pic,
            "vod_remarks": remarks,
            "vod_year": year,
            "style": {"type": "rect", "ratio": 0.7},
        }
