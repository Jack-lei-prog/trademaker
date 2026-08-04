"""pytest 配置"""
import pytest
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(autouse=True)
def setup_db():
    """每个测试前确保数据库已初始化"""
    import db
    db.init_db()
    yield
