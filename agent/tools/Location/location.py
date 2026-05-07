import requests


def get2_location() -> dict:
    """通过 IP 获取当前设备的地理位置（精确到城市）"""
    try:
        # 使用 ip-api 免费服务（无需 API Key，非商业用途）
        response = requests.get("http://ip-api.com/json/?lang=zh-CN&fields=status,country,regionName,city,lat,lon,isp,query", timeout=5)
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "success":
            return {"error": f"请求失败: {data}"}

        return {
            "国家": data.get("country"),
            "省份/地区": data.get("regionName"),
            "城市": data.get("city"),
            # "纬度": data.get("lat"),
            # "经度": data.get("lon"),
            # "ISP": data.get("isp"),
            # "IP": data.get("query"),
        }
    except requests.exceptions.RequestException as e:
        return {"error": f"网络请求异常: {e}"}
    except Exception as e:
        return {"error": f"未知异常: {e}"}


if __name__ == "__main__":
    location = get2_location()
    # for key, value in location.items():
    #     print(f"{key}: {value}")
    print(type(location))
    print(location)