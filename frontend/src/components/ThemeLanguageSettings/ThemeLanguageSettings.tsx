import React from 'react';
import {
  Card,
  Row,
  Col,
  Select,
  Switch,
  Button,
  Space,
  Typography,
  Divider,
  ColorPicker,
  message,
  Tooltip,
  Radio,
} from 'antd';
import {
  BgColorsOutlined,
  GlobalOutlined,
  SunOutlined,
  MoonOutlined,
  DesktopOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import { useThemeStore, themeStyles, type ThemeMode, type ThemeStyle } from '../../stores/themeStore';
import { useTranslation, supportedLanguages, type Language } from '../../stores/i18nStore';
import './ThemeLanguageSettings.css';

const { Title, Text } = Typography;
const { Option } = Select;

const ThemeLanguageSettings: React.FC = () => {
  const { t, language, setLanguage } = useTranslation();
  const {
    config,
    actualMode,
    setThemeMode,
    setThemeStyle,
    setCustomColors,
    resetTheme,
  } = useThemeStore();

  // 处理语言切换
  const handleLanguageChange = (newLanguage: Language) => {
    setLanguage(newLanguage);
    message.success(t('language.languageChanged'));
  };

  // 处理主题模式切换
  const handleThemeModeChange = (mode: ThemeMode) => {
    setThemeMode(mode);
    message.success(`已切换到${mode === 'light' ? '亮色' : mode === 'dark' ? '暗色' : '自动'}模式`);
  };

  // 处理主题风格切换
  const handleThemeStyleChange = (style: ThemeStyle) => {
    setThemeStyle(style);
    message.success(`已应用${themeStyles[style].name}主题`);
  };

  // 处理自定义颜色变更
  const handleCustomColorChange = (colorType: 'primary' | 'secondary' | 'accent', color: string) => {
    const newCustomColors = {
      ...config.customColors,
      [colorType]: color,
    };
    setCustomColors(newCustomColors);
  };

  // 重置主题
  const handleResetTheme = () => {
    resetTheme();
    message.success('主题已重置为默认设置');
  };

  return (
    <div className="theme-language-settings">
      {/* 语言设置 */}
      <Card className="settings-card" title={
        <Space>
          <GlobalOutlined />
          <span>{t('settings.language')}</span>
        </Space>
      }>
        <Row gutter={[16, 16]}>
          <Col span={24}>
            <div className="setting-item">
              <Text strong>{t('language.selectLanguage')}</Text>
              <Select
                value={language}
                onChange={handleLanguageChange}
                style={{ width: 200, marginLeft: 16 }}
                size="large"
              >
                {supportedLanguages.map((lang) => (
                  <Option key={lang.code} value={lang.code}>
                    <Space>
                      <span>{lang.nativeName}</span>
                      <Text type="secondary">({lang.name})</Text>
                    </Space>
                  </Option>
                ))}
              </Select>
            </div>
          </Col>
        </Row>
      </Card>

      {/* 主题设置 */}
      <Card className="settings-card" title={
        <Space>
          <BgColorsOutlined />
          <span>{t('settings.theme')}</span>
        </Space>
      }>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          {/* 主题模式 */}
          <div className="setting-section">
            <Title level={5}>{t('settings.themeMode')}</Title>
            <Radio.Group
              value={config.mode}
              onChange={(e) => handleThemeModeChange(e.target.value)}
              size="large"
            >
              <Radio.Button value="light">
                <Space>
                  <SunOutlined />
                  {t('settings.lightMode')}
                </Space>
              </Radio.Button>
              <Radio.Button value="dark">
                <Space>
                  <MoonOutlined />
                  {t('settings.darkMode')}
                </Space>
              </Radio.Button>
              <Radio.Button value="auto">
                <Space>
                  <DesktopOutlined />
                  {t('settings.autoMode')}
                </Space>
              </Radio.Button>
            </Radio.Group>
            <div className="current-mode-indicator">
              <Text type="secondary">
                当前模式: {actualMode === 'light' ? '亮色' : '暗色'}
                {config.mode === 'auto' && ' (跟随系统)'}
              </Text>
            </div>
          </div>

          <Divider />

          {/* 主题风格 */}
          <div className="setting-section">
            <Title level={5}>{t('settings.themeStyle')}</Title>
            <Row gutter={[16, 16]}>
              {Object.entries(themeStyles).map(([key, style]) => (
                <Col key={key} xs={24} sm={12} md={8} lg={6}>
                  <div
                    className={`theme-style-card ${
                      config.style === key ? 'active' : ''
                    }`}
                    onClick={() => handleThemeStyleChange(key as ThemeStyle)}
                  >
                    <div className="theme-preview">
                      <div
                        className="color-dot primary"
                        style={{ backgroundColor: style.colors.primary }}
                      />
                      <div
                        className="color-dot secondary"
                        style={{ backgroundColor: style.colors.secondary }}
                      />
                      <div
                        className="color-dot accent"
                        style={{ backgroundColor: style.colors.accent }}
                      />
                    </div>
                    <Text strong>{style.name}</Text>
                  </div>
                </Col>
              ))}
            </Row>
          </div>

          <Divider />

          {/* 自定义颜色 */}
          <div className="setting-section">
            <Title level={5}>{t('theme.customColors')}</Title>
            <Row gutter={[16, 16]}>
              <Col span={8}>
                <div className="color-picker-item">
                  <Text>{t('theme.primaryColor')}</Text>
                  <ColorPicker
                    value={config.customColors?.primary || themeStyles[config.style].colors.primary}
                    onChange={(color) => handleCustomColorChange('primary', color.toHexString())}
                    showText
                    size="large"
                  />
                </div>
              </Col>
              <Col span={8}>
                <div className="color-picker-item">
                  <Text>{t('theme.secondaryColor')}</Text>
                  <ColorPicker
                    value={config.customColors?.secondary || themeStyles[config.style].colors.secondary}
                    onChange={(color) => handleCustomColorChange('secondary', color.toHexString())}
                    showText
                    size="large"
                  />
                </div>
              </Col>
              <Col span={8}>
                <div className="color-picker-item">
                  <Text>{t('theme.accentColor')}</Text>
                  <ColorPicker
                    value={config.customColors?.accent || themeStyles[config.style].colors.accent}
                    onChange={(color) => handleCustomColorChange('accent', color.toHexString())}
                    showText
                    size="large"
                  />
                </div>
              </Col>
            </Row>
          </div>

          <Divider />

          {/* 重置按钮 */}
          <div className="setting-section">
            <Button
              icon={<ReloadOutlined />}
              onClick={handleResetTheme}
              size="large"
            >
              {t('theme.resetTheme')}
            </Button>
          </div>
        </Space>
      </Card>
    </div>
  );
};

export default ThemeLanguageSettings;