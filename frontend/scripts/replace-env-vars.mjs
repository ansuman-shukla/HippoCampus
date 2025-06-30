#!/usr/bin/env node

import { readFileSync, writeFileSync, existsSync } from 'fs';
import { config } from 'dotenv';
import path from 'path';

// Load environment variables
config();

const BACKEND_URL = process.env.VITE_BACKEND_URL;
const API_URL = process.env.VITE_API_URL;

console.log('Replacing environment variables in public files...');
console.log('BACKEND_URL:', BACKEND_URL);
console.log('API_URL:', API_URL);

// Update background.js
const backgroundPath = path.join(process.cwd(), 'dist', 'background.js');
if (existsSync(backgroundPath)) {
  let backgroundContent = readFileSync(backgroundPath, 'utf8');
  
  // Replace the BACKEND_URL constant
  backgroundContent = backgroundContent.replace(
    /const BACKEND_URL = '[^']*';/,
    `const BACKEND_URL = '${BACKEND_URL}';`
  );
  
  // Replace the API_URL constant
  backgroundContent = backgroundContent.replace(
    /const API_URL = '[^']*';/,
    `const API_URL = '${API_URL}';`
  );
  
  // Replace placeholder with actual backend URL
  backgroundContent = backgroundContent.replace(
    /__VITE_BACKEND_URL__/g,
    BACKEND_URL
  );
  
  // Replace placeholder with actual API URL
  backgroundContent = backgroundContent.replace(
    /__VITE_API_URL__/g,
    API_URL
  );
  
  writeFileSync(backgroundPath, backgroundContent);
  console.log('✓ Updated background.js with all environment variables');
}

// Update manifest.json
const manifestPath = path.join(process.cwd(), 'dist', 'manifest.json');
if (existsSync(manifestPath)) {
  let manifestContent = readFileSync(manifestPath, 'utf8');
  const manifest = JSON.parse(manifestContent);
  
  // Update host permissions
  manifest.host_permissions = manifest.host_permissions.map(permission => {
    if (permission.includes('extension-auth.vercel.app')) {
      return `${new URL(API_URL).origin}/*`;
    }
    if (permission.includes('hippocampus-cyfo.onrender.com')) {
      return `${new URL(BACKEND_URL).origin}/*`;
    }
    return permission;
  });
  
  // Update content scripts
  manifest.content_scripts = manifest.content_scripts.map(script => {
    script.matches = script.matches.map(match => {
      if (match.includes('extension-auth.vercel.app')) {
        return `${new URL(API_URL).origin}/*`;
      }
      return match;
    });
    return script;
  });
  
  writeFileSync(manifestPath, JSON.stringify(manifest, null, 2));
  console.log('✓ Updated manifest.json');
}

console.log('Environment variable replacement completed!');
