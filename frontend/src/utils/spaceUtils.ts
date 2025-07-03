/**
 * Utility functions for handling space patterns in notes
 */

/**
 * Remove space pattern from text for clean display
 * @param text - The text to clean
 * @returns Text with space pattern removed
 * 
 * Examples:
 * removeSpacePattern("This is about #books: machine learning") -> "This is about machine learning"
 * removeSpacePattern("#songs: my favorite music") -> "my favorite music"
 */
export function removeSpacePattern(text: string | null | undefined): string {
  if (!text || typeof text !== 'string') {
    return text || '';
  }

  // Pattern to match #spacename: (same as backend)
  const pattern = /\s*#[a-zA-Z0-9_-]+:\s*/g;
  
  try {
    const cleanedText = text.replace(pattern, '').trim();
    return cleanedText || text;
  } catch (error) {
    console.error('Error removing space pattern from text:', error);
    return text;
  }
}

/**
 * Extract space name from text using the pattern #spacename:
 * @param text - The text to search for space pattern
 * @returns The extracted space name or null if no pattern found
 */
export function extractSpaceFromText(text: string | null | undefined): string | null {
  if (!text || typeof text !== 'string') {
    return null;
  }

  // Pattern to match #spacename: where spacename can contain letters, numbers, underscores, hyphens
  const pattern = /#([a-zA-Z0-9_-]+):/;
  
  try {
    const match = text.match(pattern);
    if (match && match[1]) {
      const spaceName = match[1].toLowerCase().trim();
      // Validate space name (basic validation)
      if (spaceName.length > 0 && spaceName.length <= 50) {
        return spaceName;
      }
    }
    return null;
  } catch (error) {
    console.error('Error extracting space from text:', error);
    return null;
  }
} 