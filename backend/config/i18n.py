# -*- coding: utf-8 -*-
"""
国际化配置模块
提供多语言支持的配置和管理功能
"""

import os
from typing import Dict, List, Optional, Any
from enum import Enum


class SupportedLanguage(Enum):
    """支持的语言枚举"""
    CHINESE = "zh"  # 中文
    ENGLISH = "en"  # 英语
    JAPANESE = "ja"  # 日语
    KOREAN = "ko"   # 韩语
    FRENCH = "fr"   # 法语
    GERMAN = "de"   # 德语
    SPANISH = "es"  # 西班牙语
    RUSSIAN = "ru"  # 俄语
    ARABIC = "ar"   # 阿拉伯语
    PORTUGUESE = "pt"  # 葡萄牙语


class I18nConfig:
    """国际化配置类"""
    
    # 基础配置
    DEFAULT_LANGUAGE = os.getenv('DEFAULT_LANGUAGE', 'zh')
    DEFAULT_TIMEZONE = os.getenv('DEFAULT_TIMEZONE', 'Asia/Shanghai')
    DEFAULT_LOCALE = os.getenv('DEFAULT_LOCALE', 'zh_CN')
    
    # 支持的语言列表
    LANGUAGES = os.getenv('LANGUAGES', 'zh,en').split(',')
    
    # 语言检测配置
    LANGUAGE_DETECTION_METHODS = [
        'header',      # 通过HTTP头Accept-Language
        'query_param', # 通过查询参数
        'cookie',      # 通过Cookie
        'user_profile', # 通过用户配置
        'tenant_config' # 通过租户配置
    ]
    
    # 语言切换配置
    LANGUAGE_HEADER = 'Accept-Language'
    LANGUAGE_QUERY_PARAM = 'lang'
    LANGUAGE_COOKIE_NAME = 'language'
    LANGUAGE_COOKIE_MAX_AGE = 365 * 24 * 60 * 60  # 1年
    
    # 时区配置
    TIMEZONE_HEADER = 'X-Timezone'
    TIMEZONE_QUERY_PARAM = 'tz'
    TIMEZONE_COOKIE_NAME = 'timezone'
    
    # 翻译配置
    TRANSLATIONS_DIR = os.path.join(os.path.dirname(__file__), '..', 'translations')
    TRANSLATION_CACHE_ENABLED = os.getenv('TRANSLATION_CACHE_ENABLED', '1') == '1'
    TRANSLATION_CACHE_TTL = int(os.getenv('TRANSLATION_CACHE_TTL', 3600))  # 1小时
    
    # 自动翻译配置
    AUTO_TRANSLATE_ENABLED = os.getenv('AUTO_TRANSLATE_ENABLED', '0') == '1'
    AUTO_TRANSLATE_PROVIDER = os.getenv('AUTO_TRANSLATE_PROVIDER', 'baidu')  # baidu, google, deepl
    
    # 语言信息映射
    LANGUAGE_INFO = {
        'zh': {
            'name': '中文',
            'native_name': '中文',
            'code': 'zh',
            'locale': 'zh_CN',
            'timezone': 'Asia/Shanghai',
            'rtl': False,
            'flag': '🇨🇳',
            'date_format': '%Y年%m月%d日',
            'time_format': '%H:%M:%S',
            'datetime_format': '%Y年%m月%d日 %H:%M:%S',
            'currency': 'CNY',
            'currency_symbol': '¥',
            'decimal_separator': '.',
            'thousands_separator': ','
        },
        'en': {
            'name': 'English',
            'native_name': 'English',
            'code': 'en',
            'locale': 'en_US',
            'timezone': 'America/New_York',
            'rtl': False,
            'flag': '🇺🇸',
            'date_format': '%Y-%m-%d',
            'time_format': '%H:%M:%S',
            'datetime_format': '%Y-%m-%d %H:%M:%S',
            'currency': 'USD',
            'currency_symbol': '$',
            'decimal_separator': '.',
            'thousands_separator': ','
        },
        'ja': {
            'name': 'Japanese',
            'native_name': '日本語',
            'code': 'ja',
            'locale': 'ja_JP',
            'timezone': 'Asia/Tokyo',
            'rtl': False,
            'flag': '🇯🇵',
            'date_format': '%Y年%m月%d日',
            'time_format': '%H:%M:%S',
            'datetime_format': '%Y年%m月%d日 %H:%M:%S',
            'currency': 'JPY',
            'currency_symbol': '¥',
            'decimal_separator': '.',
            'thousands_separator': ','
        },
        'ko': {
            'name': 'Korean',
            'native_name': '한국어',
            'code': 'ko',
            'locale': 'ko_KR',
            'timezone': 'Asia/Seoul',
            'rtl': False,
            'flag': '🇰🇷',
            'date_format': '%Y년 %m월 %d일',
            'time_format': '%H:%M:%S',
            'datetime_format': '%Y년 %m월 %d일 %H:%M:%S',
            'currency': 'KRW',
            'currency_symbol': '₩',
            'decimal_separator': '.',
            'thousands_separator': ','
        },
        'fr': {
            'name': 'French',
            'native_name': 'Français',
            'code': 'fr',
            'locale': 'fr_FR',
            'timezone': 'Europe/Paris',
            'rtl': False,
            'flag': '🇫🇷',
            'date_format': '%d/%m/%Y',
            'time_format': '%H:%M:%S',
            'datetime_format': '%d/%m/%Y %H:%M:%S',
            'currency': 'EUR',
            'currency_symbol': '€',
            'decimal_separator': ',',
            'thousands_separator': ' '
        },
        'de': {
            'name': 'German',
            'native_name': 'Deutsch',
            'code': 'de',
            'locale': 'de_DE',
            'timezone': 'Europe/Berlin',
            'rtl': False,
            'flag': '🇩🇪',
            'date_format': '%d.%m.%Y',
            'time_format': '%H:%M:%S',
            'datetime_format': '%d.%m.%Y %H:%M:%S',
            'currency': 'EUR',
            'currency_symbol': '€',
            'decimal_separator': ',',
            'thousands_separator': '.'
        },
        'es': {
            'name': 'Spanish',
            'native_name': 'Español',
            'code': 'es',
            'locale': 'es_ES',
            'timezone': 'Europe/Madrid',
            'rtl': False,
            'flag': '🇪🇸',
            'date_format': '%d/%m/%Y',
            'time_format': '%H:%M:%S',
            'datetime_format': '%d/%m/%Y %H:%M:%S',
            'currency': 'EUR',
            'currency_symbol': '€',
            'decimal_separator': ',',
            'thousands_separator': '.'
        },
        'ru': {
            'name': 'Russian',
            'native_name': 'Русский',
            'code': 'ru',
            'locale': 'ru_RU',
            'timezone': 'Europe/Moscow',
            'rtl': False,
            'flag': '🇷🇺',
            'date_format': '%d.%m.%Y',
            'time_format': '%H:%M:%S',
            'datetime_format': '%d.%m.%Y %H:%M:%S',
            'currency': 'RUB',
            'currency_symbol': '₽',
            'decimal_separator': ',',
            'thousands_separator': ' '
        },
        'ar': {
            'name': 'Arabic',
            'native_name': 'العربية',
            'code': 'ar',
            'locale': 'ar_SA',
            'timezone': 'Asia/Riyadh',
            'rtl': True,
            'flag': '🇸🇦',
            'date_format': '%Y/%m/%d',
            'time_format': '%H:%M:%S',
            'datetime_format': '%Y/%m/%d %H:%M:%S',
            'currency': 'SAR',
            'currency_symbol': 'ر.س',
            'decimal_separator': '.',
            'thousands_separator': ','
        },
        'pt': {
            'name': 'Portuguese',
            'native_name': 'Português',
            'code': 'pt',
            'locale': 'pt_BR',
            'timezone': 'America/Sao_Paulo',
            'rtl': False,
            'flag': '🇧🇷',
            'date_format': '%d/%m/%Y',
            'time_format': '%H:%M:%S',
            'datetime_format': '%d/%m/%Y %H:%M:%S',
            'currency': 'BRL',
            'currency_symbol': 'R$',
            'decimal_separator': ',',
            'thousands_separator': '.'
        }
    }
    
    @staticmethod
    def get_supported_languages() -> List[str]:
        """获取支持的语言列表
        
        Returns:
            list: 支持的语言代码列表
        """
        return I18nConfig.LANGUAGES
    
    @staticmethod
    def get_language_info(language_code: str) -> Optional[Dict[str, Any]]:
        """获取语言信息
        
        Args:
            language_code: 语言代码
            
        Returns:
            dict: 语言信息字典，如果语言不支持则返回None
        """
        return I18nConfig.LANGUAGE_INFO.get(language_code)
    
    @staticmethod
    def is_language_supported(language_code: str) -> bool:
        """检查语言是否支持
        
        Args:
            language_code: 语言代码
            
        Returns:
            bool: 是否支持该语言
        """
        return language_code in I18nConfig.LANGUAGES
    
    @staticmethod
    def get_default_language() -> str:
        """获取默认语言
        
        Returns:
            str: 默认语言代码
        """
        return I18nConfig.DEFAULT_LANGUAGE
    
    @staticmethod
    def get_default_timezone() -> str:
        """获取默认时区
        
        Returns:
            str: 默认时区
        """
        return I18nConfig.DEFAULT_TIMEZONE
    
    @staticmethod
    def detect_language_from_request(request) -> str:
        """从请求中检测语言
        
        Args:
            request: Flask请求对象
            
        Returns:
            str: 检测到的语言代码
        """
        detected_language = None
        
        # 方法1: 从查询参数中获取
        if 'query_param' in I18nConfig.LANGUAGE_DETECTION_METHODS:
            detected_language = request.args.get(I18nConfig.LANGUAGE_QUERY_PARAM)
            if detected_language and I18nConfig.is_language_supported(detected_language):
                return detected_language
        
        # 方法2: 从Cookie中获取
        if 'cookie' in I18nConfig.LANGUAGE_DETECTION_METHODS:
            detected_language = request.cookies.get(I18nConfig.LANGUAGE_COOKIE_NAME)
            if detected_language and I18nConfig.is_language_supported(detected_language):
                return detected_language
        
        # 方法3: 从HTTP头中获取
        if 'header' in I18nConfig.LANGUAGE_DETECTION_METHODS:
            accept_language = request.headers.get(I18nConfig.LANGUAGE_HEADER, '')
            if accept_language:
                # 解析Accept-Language头
                languages = []
                for lang in accept_language.split(','):
                    lang = lang.strip().split(';')[0].split('-')[0].lower()
                    if I18nConfig.is_language_supported(lang):
                        languages.append(lang)
                if languages:
                    return languages[0]
        
        # 如果都没检测到，返回默认语言
        return I18nConfig.get_default_language()
    
    @staticmethod
    def detect_timezone_from_request(request) -> str:
        """从请求中检测时区
        
        Args:
            request: Flask请求对象
            
        Returns:
            str: 检测到的时区
        """
        # 从查询参数中获取
        timezone = request.args.get(I18nConfig.TIMEZONE_QUERY_PARAM)
        if timezone:
            return timezone
        
        # 从HTTP头中获取
        timezone = request.headers.get(I18nConfig.TIMEZONE_HEADER)
        if timezone:
            return timezone
        
        # 从Cookie中获取
        timezone = request.cookies.get(I18nConfig.TIMEZONE_COOKIE_NAME)
        if timezone:
            return timezone
        
        # 返回默认时区
        return I18nConfig.get_default_timezone()
    
    @staticmethod
    def get_locale_info(language_code: str) -> Dict[str, Any]:
        """获取语言环境信息
        
        Args:
            language_code: 语言代码
            
        Returns:
            dict: 语言环境信息
        """
        language_info = I18nConfig.get_language_info(language_code)
        if not language_info:
            language_info = I18nConfig.get_language_info(I18nConfig.get_default_language())
        
        return {
            'language': language_code,
            'locale': language_info['locale'],
            'timezone': language_info['timezone'],
            'rtl': language_info['rtl'],
            'date_format': language_info['date_format'],
            'time_format': language_info['time_format'],
            'datetime_format': language_info['datetime_format'],
            'currency': language_info['currency'],
            'currency_symbol': language_info['currency_symbol'],
            'decimal_separator': language_info['decimal_separator'],
            'thousands_separator': language_info['thousands_separator']
        }
    
    @staticmethod
    def get_translation_config() -> Dict[str, Any]:
        """获取翻译配置
        
        Returns:
            dict: 翻译配置
        """
        return {
            'translations_dir': I18nConfig.TRANSLATIONS_DIR,
            'cache_enabled': I18nConfig.TRANSLATION_CACHE_ENABLED,
            'cache_ttl': I18nConfig.TRANSLATION_CACHE_TTL,
            'auto_translate_enabled': I18nConfig.AUTO_TRANSLATE_ENABLED,
            'auto_translate_provider': I18nConfig.AUTO_TRANSLATE_PROVIDER
        }


class LocaleContext:
    """语言环境上下文管理器"""
    
    def __init__(self):
        self._current_language = None
        self._current_timezone = None
        self._locale_info = None
    
    def set_current_language(self, language_code: str):
        """设置当前语言
        
        Args:
            language_code: 语言代码
        """
        if I18nConfig.is_language_supported(language_code):
            self._current_language = language_code
            self._locale_info = I18nConfig.get_locale_info(language_code)
        else:
            self._current_language = I18nConfig.get_default_language()
            self._locale_info = I18nConfig.get_locale_info(self._current_language)
    
    def set_current_timezone(self, timezone: str):
        """设置当前时区
        
        Args:
            timezone: 时区
        """
        self._current_timezone = timezone
    
    def get_current_language(self) -> str:
        """获取当前语言
        
        Returns:
            str: 当前语言代码
        """
        return self._current_language or I18nConfig.get_default_language()
    
    def get_current_timezone(self) -> str:
        """获取当前时区
        
        Returns:
            str: 当前时区
        """
        return self._current_timezone or I18nConfig.get_default_timezone()
    
    def get_locale_info(self) -> Dict[str, Any]:
        """获取当前语言环境信息
        
        Returns:
            dict: 语言环境信息
        """
        if not self._locale_info:
            self._locale_info = I18nConfig.get_locale_info(self.get_current_language())
        return self._locale_info
    
    def clear(self):
        """清除语言环境上下文"""
        self._current_language = None
        self._current_timezone = None
        self._locale_info = None


# 全局语言环境上下文实例
locale_context = LocaleContext()


def get_current_language() -> str:
    """获取当前语言
    
    Returns:
        str: 当前语言代码
    """
    return locale_context.get_current_language()


def get_current_timezone() -> str:
    """获取当前时区
    
    Returns:
        str: 当前时区
    """
    return locale_context.get_current_timezone()


def set_current_language(language_code: str):
    """设置当前语言
    
    Args:
        language_code: 语言代码
    """
    locale_context.set_current_language(language_code)


def set_current_timezone(timezone: str):
    """设置当前时区
    
    Args:
        timezone: 时区
    """
    locale_context.set_current_timezone(timezone)


def get_locale_info() -> Dict[str, Any]:
    """获取当前语言环境信息
    
    Returns:
        dict: 语言环境信息
    """
    return locale_context.get_locale_info()