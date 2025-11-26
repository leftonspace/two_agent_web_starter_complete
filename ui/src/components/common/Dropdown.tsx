import React, { useState, useRef, useEffect } from 'react';
import { ChevronDown, Check } from 'lucide-react';

export interface DropdownOption {
  value: string;
  label: string;
  icon?: React.ReactNode;
}

export interface DropdownProps {
  options: DropdownOption[];
  value?: string;
  onChange?: (value: string) => void;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
}

export const Dropdown: React.FC<DropdownProps> = ({
  options,
  value,
  onChange,
  placeholder = 'Select...',
  disabled = false,
  className = '',
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const selectedOption = options.find((opt) => opt.value === value);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = (optionValue: string) => {
    onChange?.(optionValue);
    setIsOpen(false);
  };

  return (
    <div
      ref={dropdownRef}
      className={`dropdown ${isOpen ? 'open' : ''} ${className}`}
    >
      <button
        type="button"
        className="dropdown-trigger"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
      >
        {selectedOption ? (
          <>
            {selectedOption.icon}
            <span className="flex-1 text-left">{selectedOption.label}</span>
          </>
        ) : (
          <span className="flex-1 text-left text-tertiary">{placeholder}</span>
        )}
        <ChevronDown className={`icon transition ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      <div className="dropdown-content" role="listbox">
        {options.map((option) => (
          <div
            key={option.value}
            className={`dropdown-item ${option.value === value ? 'active' : ''}`}
            onClick={() => handleSelect(option.value)}
            role="option"
            aria-selected={option.value === value}
          >
            {option.icon}
            <span className="flex-1">{option.label}</span>
            {option.value === value && <Check className="icon-sm" />}
          </div>
        ))}
      </div>
    </div>
  );
};

export default Dropdown;
