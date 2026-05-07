"""
免费天气查询（wttr.in 主方案 + Open-Meteo 备用）
无需 API Key，直接可用，支持中文城市名。
"""
import io
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pydantic import BaseModel, Field  # 用于工具参数严格校验
from langchain_core.tools import tool

# 修复 Windows 控制台默认 GBK 编码导致的中文乱码
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")


def _fetch_json(url: str, timeout: int = 15) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "curl/7.68.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _fetch_text(url: str, timeout: int = 15) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "curl/7.68.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8").strip()


def _wmo_to_text(code: int) -> str:
    """WMO weather interpretation codes 转中文。"""
    mapping = {
        0: "晴",
        1: "大部晴朗",
        2: "多云",
        3: "阴天",
        45: "雾",
        48: "雾凇",
        51: "毛毛雨（小）",
        53: "毛毛雨（中）",
        55: "毛毛雨（大）",
        61: "小雨",
        63: "中雨",
        65: "大雨",
        71: "小雪",
        73: "中雪",
        75: "大雪",
        77: "雪粒",
        80: "阵雨（小）",
        81: "阵雨（中）",
        82: "阵雨（大）",
        85: "阵雪（小）",
        86: "阵雪（大）",
        95: "雷雨",
        96: "雷雨伴冰雹",
        99: "强雷雨伴冰雹",
    }
    return mapping.get(code, "未知天气")


def query_weather(city: str) -> dict:
    """
    输入城市名，返回天气信息字典。
    主方案使用 wttr.in（免费、无需 Key、对中文城市名友好）。
    如果 wttr.in 失败，自动回退到 Open-Meteo。
    """
    try:
        return _query_wttr(city)
    except Exception:
        # wttr.in 失败时回退到 Open-Meteo
        return _query_open_meteo(city)


def _query_wttr(city: str) -> dict:
    encoded = urllib.parse.quote(city)
    url = f"https://wttr.in/{encoded}?format=j1"
    data = _fetch_json(url)

    area = data["nearest_area"][0]
    current = data["current_condition"][0]

    def _get(area_dict, key):
        val = area_dict.get(key, [{}])
        return val[0].get("value", "") if isinstance(val, list) else str(val)

    return {
        "city": f"{_get(area, 'areaName')}, {_get(area, 'region')}, {_get(area, 'country')}".strip(", "),
        "temperature": current.get("temp_C"),
        "feels_like": current.get("FeelsLikeC"),
        "weather_text": current.get("weatherDesc", [{}])[0].get("value", ""),
        "humidity": current.get("humidity"),
        "wind_speed": current.get("windspeedKmph"),
        "wind_direction": current.get("winddir16Point"),
        "pressure": current.get("pressure"),
        "visibility": current.get("visibility"),
        "source": "wttr.in",
    }


def _query_open_meteo(city: str) -> dict:
    """备用方案：Open-Meteo。"""
    geo_url = (
        "https://geocoding-api.open-meteo.com/v1/search?"
        + urllib.parse.urlencode({
            "name": city,
            "count": 1,
            "language": "zh",
            "format": "json",
        })
    )
    geo_data = _fetch_json(geo_url)
    results = geo_data.get("results", [])
    if not results:
        raise ValueError(f"未找到城市：{city}")

    loc = results[0]
    lat = loc["latitude"]
    lon = loc["longitude"]
    name = loc.get("name", city)
    country = loc.get("country", "")
    admin1 = loc.get("admin1", "")
    full_name = " ".join(filter(None, [name, admin1, country]))

    weather_url = (
        "https://api.open-meteo.com/v1/forecast?"
        + urllib.parse.urlencode({
            "latitude": lat,
            "longitude": lon,
            "current_weather": "true",
            "timezone": "auto",
        })
    )
    weather_data = _fetch_json(weather_url)
    current = weather_data["current_weather"]

    return {
        "city": full_name,
        "temperature": current["temperature"],
        "weather_text": _wmo_to_text(current["weathercode"]),
        "wind_speed": current["windspeed"],
        "wind_direction": current["winddirection"],
        "feels_like": None,
        "humidity": None,
        "pressure": None,
        "visibility": None,
        "source": "open-meteo",
    }


def query_weather_text(city: str) -> str:
    """
    备用单行文本查询，使用 wttr.in 的简洁格式。
    """
    encoded = urllib.parse.quote(city)
    url = f"https://wttr.in/{encoded}?format=%l:+%c+%t+%w+%h+%p"
    return _fetch_text(url)



def get2_weather(city:str)->str:
    '''
    查询天气
    当用户需要查询某个城市的天气时，必须调用此工具
    参数:city(需要查询天气的城市名字)
    返回天气相关信息,ai可根据回复再组织语言回答用户
    '''
    res = ''
    try:
        info = query_weather(city)
        res += (f"城市：{info['city']}\n")
        res += (f"天气：{info['weather_text']}\n")
        res += f"温度：{info['temperature']} °C\n"
        if info.get("feels_like"):
            res += f"体感 {info['feels_like']} °C"
        if info.get("humidity"):
            res += (f"湿度：{info['humidity']}%\n")
        if info.get("wind_speed"):
            res += (f"风速：{info['wind_speed']} km/h\n")
        if info.get("wind_direction"):
            res += (f"风向：{info['wind_direction']}\n")
        if info.get("pressure"):
            res += (f"气压：{info['pressure']} hPa\n")
        if info.get("visibility"):
            res += (f"能见度：{info['visibility']} km\n")
        res += (f"来源：{info['source']}")
        return res
    except Exception as e:
        return(f"查询失败：{e}")

if __name__ == "__main__":
    iii = input('city: ')
    print(get2_weather(iii))
