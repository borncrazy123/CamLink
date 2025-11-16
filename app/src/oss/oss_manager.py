import os
import requests
import alibabacloud_oss_v2 as oss
from dotenv import load_dotenv

def getOssClient():
    # 从 .env 文件加载环境变量
    load_dotenv()

    # # 设置环境变量中的访问密钥ID和访问密钥Secret
    # print('os.environ["OSS_ACCESS_KEY_ID"]:', os.environ.get("OSS_ACCESS_KEY_ID"))
    # print('os.environ["OSS_ACCESS_KEY_SECRET"]:', os.environ.get("OSS_ACCESS_KEY_SECRET"))

    # 从命令行参数获取区域和endpoint
    region = 'cn-beijing'
    endpoint = 'oss-cn-beijing.aliyuncs.com'

    # 从环境变量中加载访问OSS所需的认证信息，用于身份验证
    credentials_provider = oss.credentials.EnvironmentVariableCredentialsProvider()

    # 使用SDK的默认配置创建配置对象，并设置认证提供者
    cfg = oss.config.load_default()
    cfg.credentials_provider = credentials_provider

    # 设置配置对象的区域属性，根据用户提供的命令行参数
    cfg.region = region

    # 如果提供了自定义endpoint，则更新配置对象中的endpoint属性
    if endpoint is not None:
        cfg.endpoint = endpoint

    # 使用上述配置初始化OSS客户端，准备与OSS交互
    client = oss.Client(cfg)

    return client

def getMultipartUploadPresignUrls(bucket, key, part_number):
    # 获取client对象
    client = getOssClient()

    # 初始化多部分上传请求
    init_pre_result = client.presign(oss.InitiateMultipartUploadRequest(
        bucket=bucket,
        key=key,
    ))
    # print("init_pre_result.url", init_pre_result.url)

    # # 需要传入的分块数量
    # part_number = 2

    return_value = {
        "upload_id": "",
        "upload_parts": []
    }

    # 发起初始化请求
    with requests.post(init_pre_result.url, headers=init_pre_result.signed_headers) as resp:
        obj = oss.InitiateMultipartUploadResult()
        
        # 需要记住这个 upload_id
        # print("obj.upload_id:", obj.upload_id)

        oss.serde.deserialize_xml(xml_data=resp.content, obj=obj)

        for partNumber in range(1, part_number + 1):
            # print("partNumber:", partNumber)
            # print("obj.upload_id:", obj.upload_id)

            # 生成预签名的上传部分请求
            up_pre_result = client.presign(oss.UploadPartRequest(
                bucket=bucket,
                key=key,
                upload_id=obj.upload_id,
                part_number=partNumber,
            ))
            # print("up_pre_result.url:", up_pre_result.url)
            return_value["upload_parts"].append({
                    "partNumber": partNumber,
                    "uploadUrl": up_pre_result.url
                })

        return_value["upload_id"] = obj.upload_id

    return return_value

def confirmCompleteMultipartUpload(bucket, key, upload_id, upload_parts):

    # 获取client对象
    client = getOssClient()

    # 要传入etag 和 part_number 列表
    oss_upload_parts = []
    for part_info in upload_parts:
        # 记录每个部分的ETag和编号
        # print("part_info:", part_info["partNumber"], part_info["etag"])
        oss_upload_parts.append(oss.UploadPart(part_number=part_info["partNumber"], etag=part_info["etag"]))

    # 按照部分编号排序
    parts = sorted(oss_upload_parts, key=lambda p: p.part_number)

    # 完成多部分上传请求
    request = oss.CompleteMultipartUploadRequest(
        bucket=bucket,
        key=key,
        upload_id=upload_id,
        complete_multipart_upload=oss.CompleteMultipartUpload(
            parts=parts
        )
    )

    # 序列化完成请求的输入
    op_input = oss.serde.serialize_input(request, oss.OperationInput(
        op_name='CompleteMultipartUpload',
        method='POST',
        bucket=request.bucket,
    ))

    # 生成预签名的完成上传请求
    complete_pre_result = client.presign(request)

    # 发送完成上传请求
    with requests.post(complete_pre_result.url, headers=complete_pre_result.signed_headers, data=op_input.body) as complete_resp:
        result = oss.CompleteMultipartUploadResult()
        oss.serde.deserialize_xml(xml_data=complete_resp.content, obj=result)
        print(f'status code: {complete_resp.status_code},'
                f' request id: {complete_resp.headers.get("x-oss-request-id")},'
                f' hash crc64: {complete_resp.headers.get("x-oss-hash-crc64ecma")},'
                f' content md5: {complete_resp.headers.get("Content-MD5")},'
                f' etag: {complete_resp.headers.get("ETag")},'
                f' content length: {complete_resp.headers.get("content-length")},'
                f' content type: {complete_resp.headers.get("Content-Type")},'
                f' url: {result.location},'
                f' encoding type: {result.encoding_type},'
                f' server time: {complete_resp.headers.get("x-oss-server-time")}'
        )

    # 打印完成请求的方法、过期时间和URL
    print(f'method: {complete_pre_result.method},'
            f' expiration: {complete_pre_result.expiration.strftime("%Y-%m-%dT%H:%M:%S.000Z")},'
            f' url: {complete_pre_result.url}'
    )

    # 打印完成请求的已签名头信息
    for key, value in complete_pre_result.signed_headers.items():
        print(f'------>>>>signed headers key: {key}, signed headers value: {value}')

def split_number(n, k):
    """
    将整数 n 平均分成 k 份，如果不能整除，则让最后一份小一点
    返回一个长度为 k 的整数列表
    """
    if k <= 0:
        raise ValueError("份数 k 必须大于 0")

    base = n // k
    remainder = n % k

    # 前 (k - 1) 份尽量多分，最后一份最小
    parts = [base + 1 if i < remainder else base for i in range(k)]
    parts.sort(reverse=True)  # 确保最后一份最小
    return parts

def testPost(presignUrls, file_path):
    presignUrls_upload_parts = presignUrls["upload_parts"]
    print("presignUrls_upload_parts.size():", len(presignUrls_upload_parts))
    # 分块大小为1MB
    # part_size = 1024 * 1024
    # part_size = 512 * 512

    # 获取文件大小
    data_size = os.path.getsize(file_path)
    print("data_size:", data_size)

    # 获取每份大小的最小整数
    part_number = len(presignUrls_upload_parts)

    upload_parts = []

    split_numbers = split_number(data_size, part_number)
    print("split_numbers:", split_numbers)

    # 打开文件进行读取
    with open(file_path, 'rb') as f:

        start = 0
        for i in range(len(split_numbers)):
            print("i:", i)
            print("start:", start)
            n = split_numbers[i]
            print("n:", n)

            up_pre_result_url = presignUrls_upload_parts[i]["uploadUrl"]            
            reader = oss.io_utils.SectionReader(oss.io_utils.ReadAtReader(f), start, n)

            # 上传分块数据
            print("up_pre_result.url:", up_pre_result_url)
            with requests.put(up_pre_result_url, data=reader) as up_result:
                print(f'status code: {up_result.status_code},'
                        f' request id: {up_result.headers.get("x-oss-request-id")},'
                        f' part number: {i + 1},'
                        f' hash crc64: {up_result.headers.get("x-oss-hash-crc64ecma")},'
                        f' content md5: {up_result.headers.get("Content-MD5")},'
                        f' etag: {up_result.headers.get("ETag")},'
                        f' server time: {up_result.headers.get("x-oss-server-time")}'
                )

                print('-'*90)
                print('up_result.headers.get("ETag"):', up_result.headers.get("ETag"))

                # 记录每个部分的ETag和编号
                upload_parts.append({
                    "partNumber": i + 1,
                    "etag": up_result.headers.get("ETag")
                })

                print('upload_parts:', upload_parts)
                print('-'*90)

            # 移动文件指针到下一个分块的起始位置
            start = start + n

    return upload_parts

# 当此脚本被直接执行时，调用main函数开始处理逻辑
if __name__ == "__main__":
    # # 定义存储桶名称和对象键
    bucket = 'camlink'
    key = "CAM-05d0d59b9d3d/test1212.mov"

    # 调用 getMultipartUploadPresignUrls 函数生成预签名的多部分上传请求
    presignUrls = getMultipartUploadPresignUrls(bucket, key, 2)
    print("upload_id from getMultipartUploadPresignUrls():", presignUrls)

    # 调用 testPost 函数上传文件的各个部分
    # 函数上传文件的各个部分
    file_path = '/Users/canvas.chenc/Desktop/test1212.mov'
    upload_parts = testPost(presignUrls, file_path)
    print("upload_parts from testPost():", upload_parts)

    # 传入 upload_id 和 对应的 part_number 和 etag 列表
    upload_id = presignUrls["upload_id"]
    # 发送完成多部分上传请求
    confirmCompleteMultipartUpload(bucket, key, upload_id, upload_parts)


# ---------------------------- CURL 示例代码 ----------------------------
# 发起分片请求：
# curl -X POST "http://121.36.170.241:8080/v1/devices/getMulUploadUrls" \
#   -H "Content-Type: application/json" \
#   -d '{
#     "client_id": "CAM-05d0d59b9d3d",
#     "fileName": "test1212.mov",
#     "partNumber": 2
#   }'

# 发起分片完成校验：
# curl -X POST "http://121.36.170.241:8080/v1/devices/confirmCmplMulUpload" \
#   -H "Content-Type: application/json" \
#   -d '{
#   "client_id": "CAM-05d0d59b9d3d",
#   "fileName": "test1212.mov",
#   "uploadId": "C566F3B59F5B4AC7B59810C78B991304",
#   "etagList": [
#     {
#       "partNumber": 1,
#       "etag": "8C9437F6C534C0C2C1D837AF06CD9724"
#     },
#     {
#       "partNumber": 2,
#       "etag": "02DA1BD8B6BFA5C5223714FF4869D90B"
#     }
#   ]
# }'
# 
# 注意：以上 CURL 示例中的 URL 和数据仅供参考，请根据实际情况进行调整。