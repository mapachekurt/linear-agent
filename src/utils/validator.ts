import { ValidationError } from '../types/agent.js';

export class Validator {
  static validateRequired(value: any, fieldName: string): ValidationError | null {
    if (value === undefined || value === null || value === '') {
      return {
        field: fieldName,
        message: `${fieldName} is required`
      };
    }
    return null;
  }

  static validateString(value: any, fieldName: string, minLength?: number, maxLength?: number): ValidationError | null {
    if (typeof value !== 'string') {
      return {
        field: fieldName,
        message: `${fieldName} must be a string`
      };
    }
    if (minLength && value.length < minLength) {
      return {
        field: fieldName,
        message: `${fieldName} must be at least ${minLength} characters`
      };
    }
    if (maxLength && value.length > maxLength) {
      return {
        field: fieldName,
        message: `${fieldName} must be at most ${maxLength} characters`
      };
    }
    return null;
  }

  static validateNumber(value: any, fieldName: string, min?: number, max?: number): ValidationError | null {
    if (typeof value !== 'number') {
      return {
        field: fieldName,
        message: `${fieldName} must be a number`
      };
    }
    if (min !== undefined && value < min) {
      return {
        field: fieldName,
        message: `${fieldName} must be at least ${min}`
      };
    }
    if (max !== undefined && value > max) {
      return {
        field: fieldName,
        message: `${fieldName} must be at most ${max}`
      };
    }
    return null;
  }

  static validateEnum(value: any, fieldName: string, allowedValues: any[]): ValidationError | null {
    if (!allowedValues.includes(value)) {
      return {
        field: fieldName,
        message: `${fieldName} must be one of: ${allowedValues.join(', ')}`
      };
    }
    return null;
  }

  static collectErrors(validations: (ValidationError | null)[]): ValidationError[] {
    return validations.filter((v): v is ValidationError => v !== null);
  }
}
