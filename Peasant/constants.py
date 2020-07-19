from re import compile as re_compile
from datetime import datetime

# =====================
# HTTP HEADER CONSTANTS
# =====================

CONTENT_TYPE_APPLICATION_JSON = 'application/json; charset=UTF-8'
ACCEPT_VND_NORMALIZED_JSON_21 = 'application/vnd.linkedin.normalized' \
                                '+json+2.1'
USER_AGENT = 'Mozilla/5.0 (iPhone; CPU iPhone OS 12_0 like Mac OS X) ' \
        'AppleWebKit/605.1.15 (KHTML, like Gecko) FxiOS/13.2b11866 Mo' \
        'bile/16A366 Safari/605.1.15'

# ============================
# REGULAR EXPRESSION CONSTANTS
# ============================

URN_RE = re_compile('urn:li:digitalmediaAsset:.+')

# =======================
# ARBITRARY API CONSTANTS
# =======================

# Media types to support image uploads
MEDIA_UPLOAD_DISPLAY_TYPES = ['PROFILE_ORIGINAL_BACKGROUND',
        'PROFILE_DISPLAY_BACKGROUND',
        'PROFILE_ORIGINAL_PHOTO',
        'PROFILE_DISPLAY_PHOTO']

# ==================
# DATETIME CONSTANTS
# ==================

NOW = datetime.now()
CYR = CURRENT_YEAR  = NOW.year
CMO = CURRENT_MONTH = NOW.month
