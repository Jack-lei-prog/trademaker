"""
用户服务 — 注册、登录、密码管理
基于 SQLite KV 存储，自动迁移旧 users.json
"""
import bcrypt


def _load_users():
    import db
    return db.load_users()


def _save_users(users):
    import db
    db.save_users(users)


def _safe_str(val, default=''):
    if val is None or not isinstance(val, str):
        return default
    return val


def get_user(email):
    return _load_users().get(email.lower().strip())


def _hash_password(password: str) -> str:
    """使用 bcrypt 哈希密码"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def _check_password(password: str, hashed: str) -> bool:
    """验证明文密码与哈希是否匹配"""
    if not hashed:
        return False
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def authenticate_user(email: str, password: str) -> dict | None:
    """验证用户密码，成功返回 user（不含 password_hash），失败返回 None"""
    users = _load_users()
    user = users.get(email.lower().strip())
    if not user:
        return None
    if not _check_password(password, user.get('password_hash', '')):
        return None
    return user
