from openwisp_utils.admin_theme.admin import OpenwispAdminSite


class CustomAdminSite(OpenwispAdminSite):
    password_change_done_template = "password_change_done.html"
