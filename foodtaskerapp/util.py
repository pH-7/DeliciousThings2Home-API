"""
Author: Pierre-Henry Soria <hi@ph7.me>
Copyright: Pierre-Henry Soria, All Rights Reserved.
"""

from django.utils import timezone
from datetime import timedelta

def get_current_weekdays():
    today = timezone.now()

    return [today + timedelta(days = i) for i in range(0 - today.weekday(), 7 - today.weekday())]
