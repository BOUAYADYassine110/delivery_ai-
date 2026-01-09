// Form validation utilities

// Individual validation functions
export const validatePhone = (value) => {
  const phoneRegex = /^\+212[5-7]\d{8}$/
  return phoneRegex.test(value)
}

export const validateEmail = (value) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(value)
}

export const validateWeight = (value) => {
  const num = parseFloat(value)
  return !isNaN(num) && num > 0 && num <= 1000
}

export const validateAddress = (value) => {
  return value && value.trim().length >= 10
}

export const validateDimensions = (length, width, height) => {
  return length > 0 && width > 0 && height > 0
}

// Validators object for form validation (returns error messages)
export const validators = {
  // Phone number validation (Moroccan format)
  phone: (value) => {
    const phoneRegex = /^\+212[5-7]\d{8}$/
    if (!value) return 'Phone number is required'
    if (!phoneRegex.test(value)) {
      return 'Invalid Moroccan phone number. Format: +212XXXXXXXXX'
    }
    return null
  },

  // Email validation
  email: (value) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!value) return 'Email is required'
    if (!emailRegex.test(value)) return 'Invalid email address'
    return null
  },

  // Required field
  required: (value, fieldName = 'This field') => {
    if (!value || (typeof value === 'string' && !value.trim())) {
      return `${fieldName} is required`
    }
    return null
  },

  // Address validation
  address: (value) => {
    if (!value || value.trim().length < 10) {
      return 'Address must be at least 10 characters'
    }
    return null
  },

  // Weight validation
  weight: (value) => {
    const num = parseFloat(value)
    if (isNaN(num)) return 'Weight must be a number'
    if (num <= 0) return 'Weight must be greater than 0'
    if (num > 500) return 'Weight cannot exceed 500 kg'
    return null
  },

  // Name validation
  name: (value) => {
    if (!value || value.trim().length < 2) {
      return 'Name must be at least 2 characters'
    }
    if (value.length > 100) {
      return 'Name cannot exceed 100 characters'
    }
    return null
  },

  // City validation
  city: (value) => {
    const validCities = ['Casablanca', 'Rabat', 'Marrakech', 'Agadir', 'El Jadida', 'Salé']
    if (!value) return 'City is required'
    if (!validCities.includes(value)) {
      return 'Please select a valid city'
    }
    return null
  }
}

// Format phone number as user types
export const formatPhoneNumber = (value) => {
  const digits = value.replace(/\D/g, '')
  
  if (digits.startsWith('212')) {
    return '+' + digits.slice(0, 12)
  }
  
  if (digits.startsWith('0')) {
    return '+212' + digits.slice(1, 10)
  }
  
  if (digits.length > 0) {
    return '+212' + digits.slice(0, 9)
  }
  
  return value
}
