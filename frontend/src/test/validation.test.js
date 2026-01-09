import { describe, it, expect, beforeEach } from 'vitest'
import { validatePhone, validateEmail, validateWeight, formatPhoneNumber } from '../utils/validation'

describe('Validation Utils', () => {
  describe('validatePhone', () => {
    it('should validate correct Moroccan phone numbers', () => {
      expect(validatePhone('+212612345678')).toBe(true)
      expect(validatePhone('+212712345678')).toBe(true)
    })

    it('should reject invalid phone numbers', () => {
      expect(validatePhone('123456')).toBe(false)
      expect(validatePhone('+1234567890')).toBe(false)
      expect(validatePhone('')).toBe(false)
    })
  })

  describe('validateEmail', () => {
    it('should validate correct email addresses', () => {
      expect(validateEmail('test@example.com')).toBe(true)
      expect(validateEmail('user.name@domain.co.ma')).toBe(true)
    })

    it('should reject invalid email addresses', () => {
      expect(validateEmail('invalid')).toBe(false)
      expect(validateEmail('@example.com')).toBe(false)
      expect(validateEmail('')).toBe(false)
    })
  })

  describe('validateWeight', () => {
    it('should validate correct weights', () => {
      expect(validateWeight(1)).toBe(true)
      expect(validateWeight(50.5)).toBe(true)
      expect(validateWeight(1000)).toBe(true)
    })

    it('should reject invalid weights', () => {
      expect(validateWeight(0)).toBe(false)
      expect(validateWeight(-5)).toBe(false)
      expect(validateWeight(1001)).toBe(false)
    })
  })

  describe('formatPhoneNumber', () => {
    it('should format phone numbers correctly', () => {
      expect(formatPhoneNumber('0612345678')).toBe('+212612345678')
      expect(formatPhoneNumber('612345678')).toBe('+212612345678')
    })

    it('should handle already formatted numbers', () => {
      expect(formatPhoneNumber('+212612345678')).toBe('+212612345678')
    })
  })
})
