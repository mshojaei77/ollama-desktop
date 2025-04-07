import React, { useState, useRef, useEffect } from 'react'

interface Option {
  value: string
  label: string
}

interface StyledSelectProps {
  options: Option[]
  defaultValue?: string
  onChange?: (value: string) => void
  className?: string
}

const StyledSelect: React.FC<StyledSelectProps> = ({
  options,
  defaultValue,
  onChange,
  className = ''
}) => {
  const [isOpen, setIsOpen] = useState(false)
  const [selectedOption, setSelectedOption] = useState<Option | undefined>(
    options.find(option => option.value === defaultValue) || options[0]
  )
  const selectRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (selectRef.current && !selectRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [])

  const handleSelect = (option: Option) => {
    setSelectedOption(option)
    setIsOpen(false)
    if (onChange) {
      onChange(option.value)
    }
  }

  return (
    <div 
      className={`relative inline-block text-left ${className}`}
      ref={selectRef}
    >
      <div>
        <button
          type="button"
          className="inline-flex justify-between items-center w-full rounded-md border border-border bg-background px-3 py-1 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
          onClick={() => setIsOpen(!isOpen)}
        >
          <span>{selectedOption?.label}</span>
          <svg 
            className="-mr-1 ml-2 h-4 w-4" 
            xmlns="http://www.w3.org/2000/svg" 
            viewBox="0 0 20 20" 
            fill="currentColor"
          >
            <path 
              fillRule="evenodd" 
              d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" 
              clipRule="evenodd" 
            />
          </svg>
        </button>
      </div>

      {isOpen && (
        <div className="z-10 origin-top-right absolute left-0 right-0 mt-1 rounded-md shadow-lg bg-background border border-border ring-1 ring-black ring-opacity-5 focus:outline-none">
          <div className="py-1 max-h-60 overflow-auto">
            {options.map((option) => (
              <div
                key={option.value}
                className={`block px-4 py-2 text-sm cursor-pointer hover:bg-accent hover:text-accent-foreground ${
                  selectedOption?.value === option.value ? 'bg-accent/50' : ''
                }`}
                onClick={() => handleSelect(option)}
              >
                {option.label}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default StyledSelect 