"""mineru解析文档入口"""

from folioAgent.config import require_env
from zipfile import ZipFile
import requests,time,io


TOKEN = require_env("MINERU_API_KEY")
header = {"Content-type": "application/json", "Authorization": f"Bearer {TOKEN}"}
# 上传文件
def upload_files()->dict[str,str|int|list]:
    url = require_env("MINERU_URL") + "/v4/file-urls/batch"
    upload_url = [
        {
            "name": "langgraph-core-concepts",
            "url": "/Users/fang/learning/folio-agent/data/corpus/langgraph-core-concepts.docx",
        }
    ]
    data = {
        "files": [{"name": files["name"]} for files in upload_url],
        "model_version": "vlm",
    }
    try:
        response = requests.post(url, headers=header, data=data)
        response.raise_for_status()
        file_upload_result = response.json()

        if file_upload_result["code"] != 0:
            print(f"上传文件失败:{file_upload_result['msg']}")
            return {"code": 403, "msg": f"上传文件失败:{file_upload_result['msg']}"}

        data = file_upload_result["data"]
        batch_id = file_upload_result["batch_id"]
        file_urls = data["file_urls"]

        upload_errors = []

        
        for index, file_url in enumerate(file_urls):
            with open(upload_url[index]["url"],"rb") as f:
                upload_response = requests.put(file_url, data=f)

                if upload_response.status_code != 200:
                    upload_errors.append(upload_url[index]["name"])

        return {
            "code": 200,
            'upload_errors':len(upload_errors),
            "msg":f"""
                    {
                        "部分上传失败，请重新上传{'\n'.join(upload_errors)}"
                        if len(upload_errors)>0
                        else "上传成功"
                    }
                """,'batch_id':batch_id}

    except Exception as err:
        print(err)
        return {"code": 403, "msg": f"上传文件失败:{err}"}

# 查询上传结果
def find_upload_status(batch_id)->str|None:
    url = require_env("MINERU_URL") + f"/v4/extract-results/batch/{batch_id}"
    while True:
        respones=requests.get(url,headers=header)
        respones.raise_for_status() 
        result = respones.json()
        if result['code'] != 0:
            return None
        
        data = result['data']
        extract_result = data['extract_result']
        if extract_result['state']=='done':
            return extract_result['full_zip_url']
        if extract_result['state']=='failed':
            raise RuntimeError(data.get("err_msg", "解析失败"))
        time.sleep(5)

# 下载zip包并解析
def download_and_show(zip_url):
    url =requests.get(zip_url)
    with ZipFile(io.BytesIO(url.content),"r") as z:
        files = z.namelist()


def main():
    result:dict = upload_files()
    if result['code']==200:
        batch_id = result['batch_id']
        zip_url = find_upload_status(batch_id)