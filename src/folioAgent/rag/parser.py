"""mineru解析文档入口"""

from folioAgent.config import require_env
from zipfile import ZipFile
from folioAgent.config import upload_url
import requests, time, io

TOKEN = require_env("MINERU_API_KEY")
header = {"Content-type": "application/json", "Authorization": f"Bearer {TOKEN}"}
results = []


# 上传文件
def upload_files() -> dict[str, str | int | list]:
    url = require_env("MINERU_URL") + "/v4/file-urls/batch"

    data = {
        "files": [
            {"name": files["name"], "data_id": files["data_id"]} for files in upload_url
        ],
        "model_version": "vlm",
    }
    try:
        response = requests.post(url, headers=header, json=data)
        response.raise_for_status()
        file_upload_result = response.json()

        if file_upload_result["code"] != 0:
            print(f"上传文件失败:{file_upload_result['msg']}")
            return {"code": 403, "msg": f"上传文件失败:{file_upload_result['msg']}"}
       
        data = file_upload_result["data"]
        batch_id = data["batch_id"]
        file_urls = data["file_urls"]

        upload_errors = []

        for index, file_url in enumerate(file_urls):
            with open(upload_url[index]["url"], "rb") as f:
                upload_response = requests.put(file_url, data=f)
                if upload_response.status_code != 200:
                    upload_errors.append(upload_url[index]["name"])

        return {
            "code": 200,
            "upload_errors": len(upload_errors),
            "msg": f"""
                    {
                        "部分上传失败，请重新上传{'\n'.join(upload_errors)}"
                        if len(upload_errors)>0
                        else "上传成功"
                    }
                """,
            "batch_id": batch_id,
        }

    except Exception as err:
        print(err,'err')
        return {"code": 403, "msg": f"上传文件失败:{err}"}


# 查询上传结果
def find_upload_status(batch_id) -> list[dict[str, str]]:
    url = require_env("MINERU_URL") + f"/v4/extract-results/batch/{batch_id}"
    while True:
        respones = requests.get(url, headers=header)
        respones.raise_for_status()
        result = respones.json()
        if result["code"] != 0:
            return []

        data = result["data"]
        extract_result = data["extract_result"]
        if not extract_result:
            time.sleep(5)
            continue

        for result in extract_result:
            if result["state"] != "failed" and result["state"] != "done":
                break
        else:
            return extract_result

        time.sleep(5)


# 下载zip包并解析
def download_and_show(zip_url):
    zip = requests.get(zip_url)
    with ZipFile(io.BytesIO(zip.content), "r") as z:
        files = z.namelist()
        content_list = [
            z.read(file).decode("utf-8") for file in files if file.endswith(".md")
        ]
        return content_list


def parser() -> list:
    result: dict = upload_files()
    content_list = [] # [{"data_id":1212,"content":[]}]
    if result["code"] == 200:
        batch_id = result["batch_id"]
        extract_result = find_upload_status(batch_id)
        if extract_result:
            for data in extract_result:
                content_list.append(
                    {
                        "data_id": data.get("data_id"),
                        "content": download_and_show(data.get("full_zip_url"))[0],
                    }
                )
    return content_list
