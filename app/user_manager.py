class AppUser:
    def __init__(self, username: str, email: str, fullname: str, is_admin: bool):
        self.username = username
        self.email = email
        self.fullname = fullname
        self.is_admin = is_admin

    def __repr__(self):
        return f"AppUser(username='{self.username}', fullname='{self.fullname}', is_admin={self.is_admin})"
