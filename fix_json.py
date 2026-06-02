import json
import re

file_path = '/Users/petercoldicott/Library/Application Support/JetBrains/PyCharm2026.1/scratches/scratch_1.json'
with open(file_path, 'r') as f:
    content = f.read()

print(f"Original content first 500 chars: {content[:500]}")

# The issue is likely multiline strings that are not triple-quoted.
# We will try to join lines that don't end with a comma or brace.

lines = content.split('\n')
fixed_lines = []
for line in lines:
    stripped = line.strip()
    if not stripped:
        continue
    # If the line doesn't end with a "safe" character and isn't the start of a structure, 
    # it might be a continuation of a string.
    if fixed_lines and not (fixed_lines[-1].strip().endswith(',') or 
                            fixed_lines[-1].strip().endswith('{') or 
                            fixed_lines[-1].strip().endswith('[') or
                            fixed_lines[-1].strip().endswith(':') or
                            stripped.startswith("'") or
                            stripped.startswith('{') or
                            stripped.startswith('}') or
                            stripped.startswith('[') or
                            stripped.startswith(']')):
         fixed_lines[-1] = fixed_lines[-1].rstrip() + " " + stripped
    else:
         fixed_lines.append(line)

content = "\n".join(fixed_lines)

# Now try to replace True/False/None and single quotes
content = content.replace(': False', ': false').replace(': True', ': true').replace(': None', ': null')

# The '' in the original file is a literal single quote inside a single-quoted string.
# We should replace it with something safe BEFORE we do the regex replacement.
content = content.replace("''", "\\'")

def fix_quotes(match):
    s = match.group(0)
    inner = s[1:-1]
    # In the original file, it was '' for single quote. We replaced it with \'
    # Now we need to escape double quotes that were in the original string.
    inner = inner.replace('"', '\\"')
    inner = inner.replace('\n', ' ') 
    return '"' + inner + '"'

content = re.sub(r"'[^']*'", fix_quotes, content, flags=re.DOTALL)

# Pre-process to handle double-double quotes that might be present in the original or created by join
# If we have something like " "required": false" it means we have a quote that wasn't escaped.
# Let's try to replace " with \" ONLY if it's not at a "structure" position, but that's hard.
# Actually, if we have "something" "required", the middle quotes are the problem.

content = content.replace('", "', '",@@@"') # Protect valid delimiters
content = content.replace('": ', '":@@@')   # Protect valid delimiters
content = content.replace('{"', '{@@@"')   # Protect valid delimiters
content = content.replace('"}', '"@@@}')   # Protect valid delimiters
content = content.replace('["', '[@@@"')   # Protect valid delimiters
content = content.replace('"]', '"@@@]')   # Protect valid delimiters

# Now we might have some remaining double quotes that are NOT part of the structure
# But wait, the regex replaced ALL ' with ". 
# So any " that was NOT created by the regex (i.e. was already in the string) should be escaped.
# But we already did inner.replace('"', '\\"') in fix_quotes.

# Let's look at the context again:
# trial.\", "required": false
# It seems my join logic might have joined something it shouldn't, or the regex missed something.

try:
    data = json.loads(content.replace('@@@', ''))
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)
    print("Successfully refactored JSON using regex and json.loads")
except Exception as e:
    print(f"JSON load failed: {e}")
    # Show a snippet of the problematic area
    pos = int(re.search(r"char (\d+)", str(e)).group(1))
    print(f"Context at {pos}: {content[max(0, pos-50):min(len(content), pos+50)]}")
