import React, { useState, useRef, useEffect } from 'react';
import { Input, Tag, Space } from 'antd';
import { CloseOutlined } from '@ant-design/icons';
import './TagInput.css';

interface TagInputProps {
  value?: string[];
  onChange?: (tags: string[]) => void;
  placeholder?: string;
  maxTags?: number;
  disabled?: boolean;
  className?: string;
}

const TagInput: React.FC<TagInputProps> = ({
  value = [],
  onChange,
  placeholder = '输入标签，用分号(;)分隔',
  maxTags = 10,
  disabled = false,
  className = ''
}) => {
  const [inputValue, setInputValue] = useState('');
  const [inputVisible, setInputVisible] = useState(false);
  const inputRef = useRef<any>(null);

  useEffect(() => {
    if (inputVisible) {
      inputRef.current?.focus();
    }
  }, [inputVisible]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    
    // 检查是否包含分号
    if (newValue.includes(';')) {
      const parts = newValue.split(';');
      const newTags = parts.slice(0, -1)
        .map(tag => tag.trim())
        .filter(tag => tag && !value.includes(tag));
      
      if (newTags.length > 0 && value.length + newTags.length <= maxTags) {
        const updatedTags = [...value, ...newTags];
        onChange?.(updatedTags);
      }
      
      // 保留最后一部分作为新的输入值
      setInputValue(parts[parts.length - 1]);
    } else {
      setInputValue(newValue);
    }
  };

  const handleInputConfirm = () => {
    const trimmedValue = inputValue.trim();
    if (trimmedValue && !value.includes(trimmedValue) && value.length < maxTags) {
      onChange?.([...value, trimmedValue]);
    }
    setInputValue('');
    setInputVisible(false);
  };

  const handleTagClose = (removedTag: string) => {
    const newTags = value.filter(tag => tag !== removedTag);
    onChange?.(newTags);
  };

  const showInput = () => {
    setInputVisible(true);
  };

  const handleInputBlur = () => {
    handleInputConfirm();
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleInputConfirm();
    } else if (e.key === 'Escape') {
      setInputValue('');
      setInputVisible(false);
    }
  };

  return (
    <div className={`tag-input-container ${className}`}>
      <Space size={[8, 8]} wrap>
        {value.map((tag, index) => (
          <Tag
            key={tag}
            closable={!disabled}
            closeIcon={<CloseOutlined />}
            onClose={() => handleTagClose(tag)}
            className="custom-tag"
          >
            {tag}
          </Tag>
        ))}
        
        {inputVisible ? (
          <Input
            ref={inputRef}
            type="text"
            size="small"
            className="tag-input"
            value={inputValue}
            onChange={handleInputChange}
            onBlur={handleInputBlur}
            onKeyDown={handleKeyPress}
            placeholder={placeholder}
            disabled={disabled}
          />
        ) : (
          !disabled && value.length < maxTags && (
            <Tag
              className="add-tag"
              onClick={showInput}
            >
              + 添加标签
            </Tag>
          )
        )}
      </Space>
      
      {!inputVisible && (
        <div className="tag-input-help">
          <span className="help-text">提示: 输入标签后按分号(;)快速添加</span>
        </div>
      )}
    </div>
  );
};

export default TagInput;