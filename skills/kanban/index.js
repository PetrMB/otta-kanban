#!/usr/bin/env node
// kanban skill runner
const fs = require('fs');
const path = require('path');

const WORKSPACE_DIR = process.env.OPENCLAW_WORKSPACE || '/Users/otto/.openclaw/workspace';
const KANBAN_DIR = path.join(WORKSPACE_DIR, 'projects', 'kanban');

function parseMarkdown(file) {
  const content = fs.readFileSync(file, 'utf-8');
  const lines = content.split('\n');
  
  // Find tasks (lines starting with - or ##)
  const tasks = [];
  let currentSection = 'unknown';
  
  for (const line of lines) {
    const h4Match = line.match(/^#### (.+)$/);
    if (h4Match) {
      currentSection = h4Match[1].trim();
      continue;
    }
    
    const taskMatch = line.match(/^- (.+)$/);
    if (taskMatch) {
      tasks.push({ section: currentSection, content: taskMatch[1].trim() });
    }
  }
  
  return { tasks, currentSection };
}

function addTask(section, task) {
  const file = path.join(KANBAN_DIR, `${section}.md`);
  if (!fs.existsSync(file)) {
    console.error(`Section "${section}" not found. Use: backlog, in-progress, done`);
    process.exit(1);
  }
  
  const content = fs.readFileSync(file, 'utf-8');
  const lines = content.split('\n');
  
  // Find last task line or insert after header
  let insertIdx = lines.length;
  for (let i = lines.length - 1; i >= 0; i--) {
    if (lines[i].startsWith('- ') || lines[i].startsWith('## ') || lines[i].startsWith('### ')) {
      insertIdx = i + 1;
      break;
    }
  }
  
  lines.splice(insertIdx, 0, `- ${task}`);
  
  fs.writeFileSync(file, lines.join('\n'));
  console.log(`Added "${task}" to ${section}`);
}

function removeTask(section, task) {
  const file = path.join(KANBAN_DIR, `${section}.md`);
  if (!fs.existsSync(file)) {
    console.error(`Section "${section}" not found`);
    process.exit(1);
  }
  
  let content = fs.readFileSync(file, 'utf-8');
  const lines = content.split('\n');
  
  // Find and remove matching task
  const filtered = lines.filter(line => !line.includes(task));
  
  if (filtered.length === lines.length) {
    console.log(`Task "${task}" not found in ${section}`);
    return;
  }
  
  fs.writeFileSync(file, filtered.join('\n'));
  console.log(`Removed "${task}" from ${section}`);
}

function showBoard() {
  const sections = ['backlog', 'in-progress', 'done'];
  
  for (const section of sections) {
    const file = path.join(KANBAN_DIR, `${section}.md`);
    if (!fs.existsSync(file)) continue;
    
    const content = fs.readFileSync(file, 'utf-8');
    console.log(`\n=== ${section.toUpperCase()} ===`);
    console.log(content);
  }
}

function sync() {
  // Build HTML from markdown files
  const sections = {
    backlog: 'Backlog',
    'in-progress': 'Rozpracováno',
    done: 'Hotovo'
  };
  
  let html = `<!DOCTYPE html>\n<html lang="cs">\n<head>\n  <meta charset="UTF-8" />\n  <meta name="viewport" content="width=device-width, initial-scale=1.0" />\n  <title>Kanban — Otto Honeger</title>\n  <style>\n    * { box-sizing: border-box; margin: 0; padding: 0; }\n    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f5f7fa; padding: 20px; }\n    h1 { text-align: center; margin-bottom: 30px; color: #2c3e50; }\n    .board { display: flex; gap: 20px; justify-content: center; flex-wrap: wrap; }\n    .column { background: #e5e7eb; border-radius: 8px; padding: 15px; min-width: 350px; max-width: 450px; flex: 1; }\n    .column h2 { margin-bottom: 15px; padding-bottom: 10px; border-bottom: 2px solid #d1d5db; font-size: 1.1rem; }\n    .column.backlog h2 { border-color: #fbbf24; color: #b45309; }\n    .column.rozpracovano h2 { border-color: #3b82f6; color: #1e40af; }\n    .column.done h2 { border-color: #22c55e; color: #15803d; }\n    .task { background: white; padding: 12px; border-radius: 6px; margin-bottom: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }\n    .task h4 { margin-bottom: 6px; font-size: 0.95rem; }\n    .task p { color: #4b5563; margin-bottom: 6px; }\n    .task .priority-badge { display: inline-block; padding: 2px 6px; border-radius: 4px; font-size: 0.75rem; margin-right: 8px; }\n    .priority-high { background: #dcfce7; color: #166534; }\n    .priority-medium { background: #fef3c7; color: #92400e; }\n    .task .status { color: #6b7280; font-size: 0.8rem; }\n  </style>\n</head>\n<body>\n  <h1>📝 Otto Honeger — Kanban</h1>\n  <div class="board">\n`;
  
  for (const [dir, label] of Object.entries(sections)) {
    const file = path.join(KANBAN_DIR, `${dir}.md`);
    if (!fs.existsSync(file)) continue;
    
    const content = fs.readFileSync(file, 'utf-8');
    const tasks = content.split('\n').filter(l => l.startsWith('- ')).map(l => l.substring(2));
    
    let columnClass = dir.replace('-', '');
    if (dir === 'in-progress') columnClass = 'rozpracovano';
    
    html += `    <div class="column ${columnClass}">\n`;
    html += `      <h2>${getEmoji(dir)} ${label}</h2>\n`;
    
    for (const task of tasks) {
      // Parse emoji and content
      const emojiMatch = task.match(/^([^\s]+)\s+(.+)$/);
      if (emojiMatch) {
        const emoji = emojiMatch[1];
        const text = emojiMatch[2];
        html += `      <div class="task"><h4>${emoji} ${text}</h4><p class="status"></p></div>\n`;
      } else {
        html += `      <div class="task"><h4>${task}</h4><p class="status"></p></div>\n`;
      }
    }
    
    html += `    </div>\n`;
  }
  
  html += `  </div>\n</body>\n</html>\n`;
  
  const htmlFile = path.join(KANBAN_DIR, 'kanban.html');
  fs.writeFileSync(htmlFile, html);
  console.log('HTML regenerated: kanban.html');
  
  // Commit changes
  const { execSync } = require('child_process');
  try {
    execSync('git add projects/kanban/', { cwd: WORKSPACE_DIR, stdio: 'pipe' });
    execSync('git commit -m "Update kanban board"', { cwd: WORKSPACE_DIR, stdio: 'pipe' });
    console.log('Changes committed to git');
    console.log('Run "git push" to sync to otto.honeger.com');
  } catch (err) {
    // No changes to commit
    console.log('No changes to commit');
  }
}

function getEmoji(dir) {
  const emojis = {
    backlog: '📝',
    'in-progress': '🚀',
    done: '✅'
  };
  return emojis[dir] || '📋';
}

// CLI
const args = process.argv.slice(2);
const [command, section, task] = args;

switch (command) {
  case 'add':
    if (!section || !task) {
      console.log('Usage: node kanban.js add [section] [task]');
      process.exit(1);
    }
    addTask(section, task);
    break;
  case 'remove':
    if (!section || !task) {
      console.log('Usage: node kanban.js remove [section] [task]');
      process.exit(1);
    }
    removeTask(section, task);
    break;
  case 'show':
    showBoard();
    break;
  case 'sync':
    sync();
    break;
  default:
    console.log(`Usage:
  node kanban.js add [section] [task]    - Add task to section
  node kanban.js remove [section] [task] - Remove task from section
  node kanban.js show                    - Display all sections
  node kanban.js sync                    - Build HTML and commit to git

Sections: backlog, in-progress, done`);
}
