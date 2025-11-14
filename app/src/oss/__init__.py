"""
oss管理模块
用于管理oss文件上传等功能
"""
from .oss_manager import getMultipartUploadPresignUrls, confirmCompleteMultipartUpload
    
__all__ = ['getMultipartUploadPresignUrls', 'confirmCompleteMultipartUpload']

