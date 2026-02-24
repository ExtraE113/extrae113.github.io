#!/usr/bin/env python3
"""
Update the resume section of index.html from Resume_Ezra_Newman.md.
Parses the MD table format, extracts structured resume data,
and regenerates the resume <ol> in index.html to match.
"""

import re
import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MD_PATH = os.path.join(SCRIPT_DIR, 'Resume_Ezra_Newman.md')
HTML_PATH = os.path.join(SCRIPT_DIR, 'index.html')


def read_file(path):
    with open(path, encoding='utf-8') as f:
        return f.read()


def write_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)


def clean_md_inline(text):
    """Remove inline markdown formatting, preserving the actual text."""
    # Remove bold markers
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    # Remove italic markers
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    # Remove markdown links, keep display text
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    # Replace escaped hyphens
    text = text.replace('\\-', '-')
    # Normalize runs of whitespace to single space
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def parse_md():
    """Parse the MD resume table and return structured data."""
    md = read_file(MD_PATH)
    lines = md.strip().split('\n')

    # Find table data rows (not alignment/separator rows)
    data_rows = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('|') and ':----' not in stripped:
            data_rows.append(stripped)

    if len(data_rows) < 2:
        print(f"ERROR: Expected at least 2 table data rows, found {len(data_rows)}")
        sys.exit(1)

    header_row = data_rows[0]
    body_row = data_rows[1]

    # Header row layout: | Name | sidebar (skills, activities, morning) |
    header_cells = header_row.split('|')
    sidebar_raw = header_cells[2].strip() if len(header_cells) > 2 else ''

    # Body row layout: | main content (education + experience) |  |
    body_cells = body_row.split('|')
    main_raw = body_cells[1].strip() if len(body_cells) > 1 else ''

    # --- Parse sidebar sections ---
    skills_match = re.search(r'SKILLS\s+(.*?)\s*ACTIVITIES', sidebar_raw, re.DOTALL)
    skills_raw = skills_match.group(1).strip() if skills_match else ''

    # Split individual skills on word boundaries:
    # each skill starts with one of these capitalized words
    skill_items = re.split(
        r'(?<=[a-z\)]) (?=Practiced|Highly|Fluent|Experienced|Proficient|Skilled)',
        skills_raw
    )
    skills = [clean_md_inline(s) for s in skill_items if s.strip()]

    activities_match = re.search(
        r'ACTIVITIES\s+(.*?)\s*GETS ME UP IN THE MORNING', sidebar_raw, re.DOTALL
    )
    activities = clean_md_inline(activities_match.group(1)) if activities_match else ''

    morning_match = re.search(r'GETS ME UP IN THE MORNING\s+(.*?)$', sidebar_raw, re.DOTALL)
    morning = clean_md_inline(morning_match.group(1)) if morning_match else ''

    # --- Split main content into education / experience ---
    work_split = re.search(r'\*\*WORK EXPERIENCE\s+', main_raw)
    if work_split:
        education_raw = main_raw[:work_split.start()].strip()
        experience_raw = main_raw[work_split.start():].strip()
    else:
        education_raw = main_raw
        experience_raw = ''

    education = parse_section_entries(education_raw, 'EDUCATION')
    experience = parse_section_entries(experience_raw, 'WORK EXPERIENCE')

    return {
        'skills': skills,
        'activities': activities,
        'morning': morning,
        'education': education,
        'experience': experience,
    }


def parse_section_entries(raw, section_header):
    """Parse individual entries from a section using bold markers as delimiters."""
    entries = []
    bold_pattern = re.compile(r'\*\*(.+?)\*\*')
    matches = list(bold_pattern.finditer(raw))

    for i, match in enumerate(matches):
        title = match.group(1).strip()

        # Strip the section header prefix from the first entry's title
        # e.g. "EDUCATION BlueDot" → "BlueDot"
        if title.startswith(section_header + ' '):
            title = title[len(section_header):].strip()
        elif title.startswith(section_header):
            title = title[len(section_header):].strip()

        if not title:
            continue

        # Everything between this bold match and the next one
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(raw)
        rest = raw[start:end].strip()

        # Look for em-dash followed by italic subtitle(s)
        subtitle = ''
        em_dash_match = re.match(r'\s*—\s*', rest)
        if em_dash_match:
            after_dash = rest[em_dash_match.end():]
            subtitle_parts = []
            while True:
                italic_match = re.match(r'\*([^*]+)\*\s*', after_dash)
                if italic_match:
                    subtitle_parts.append(italic_match.group(1))
                    after_dash = after_dash[italic_match.end():]
                else:
                    break
            subtitle = ' '.join(subtitle_parts) if subtitle_parts else ''
            rest = after_dash.strip()

        body = clean_md_inline(rest)

        entries.append({
            'title': title,
            'subtitle': subtitle,
            'body': body,
        })

    return entries


def split_edu_description(desc):
    """Split an education entry description into logical paragraphs."""
    parts = []
    remaining = desc

    # GPA line
    gpa_match = re.match(r'(GPA:\s*\S+)\s*(.*)', remaining, re.DOTALL)
    if gpa_match:
        parts.append(gpa_match.group(1))
        remaining = gpa_match.group(2).strip()

    # Relevant CS Coursework (up to the period)
    cs_match = re.match(r'(Relevant CS Coursework:.*?\.)\s*(.*)', remaining, re.DOTALL)
    if cs_match:
        parts.append(cs_match.group(1))
        remaining = cs_match.group(2).strip()

    # Relevant Philosophy Coursework (up to the period)
    phil_match = re.match(
        r'(Relevant Philosophy Coursework:.*?\.)\s*(.*)', remaining, re.DOTALL
    )
    if phil_match:
        parts.append(phil_match.group(1))
        remaining = phil_match.group(2).strip()

    if remaining:
        parts.append(remaining)

    return parts if parts else [desc]


DATE_RE = re.compile(
    r'^((?:January|February|March|April|May|June|July|August|September|'
    r'October|November|December)\s+\d{4}\s*-\s*'
    r'(?:Present|(?:January|February|March|April|May|June|July|August|'
    r'September|October|November|December)\s+\d{4}))\s*(.*)',
    re.DOTALL,
)


def generate_entry_html(entry, tag_name, is_education=False):
    """Generate HTML lines for one resume entry."""
    lines = []
    lines.append('\t\t\t\t<li>')
    lines.append(f'\t\t\t\t\t<h3 class="tag">{tag_name}</h3>')

    title = entry['title']
    subtitle = entry['subtitle']
    body = entry['body']

    if subtitle:
        lines.append(f'\t\t\t\t\t<h4>{title}&mdash;{subtitle}</h4>')
    elif title:
        lines.append(f'\t\t\t\t\t<h4>{title}</h4>')

    if body:
        date_match = DATE_RE.match(body)
        if date_match:
            date_str = date_match.group(1).strip()
            desc = date_match.group(2).strip()
            lines.append(f'\t\t\t\t\t<p>{date_str}</p>')
            if desc:
                if is_education:
                    for part in split_edu_description(desc):
                        lines.append(f'\t\t\t\t\t<p>{part}</p>')
                else:
                    lines.append(f'\t\t\t\t\t<p>{desc}</p>')
        else:
            # No date found — treat entire body as description
            if is_education:
                for part in split_edu_description(body):
                    lines.append(f'\t\t\t\t\t<p>{part}</p>')
            else:
                lines.append(f'\t\t\t\t\t<p>{body}</p>')

    lines.append('\t\t\t\t</li>')
    return lines


def generate_resume_html(data):
    """Build the full inner HTML for the resume <ol>."""
    all_lines = []

    # Education entries
    for entry in data['education']:
        all_lines.extend(generate_entry_html(entry, 'education', is_education=True))

    # Experience entries
    for entry in data['experience']:
        all_lines.extend(generate_entry_html(entry, 'experience', is_education=False))

    # Skills
    all_lines.append('\t\t\t\t<li>')
    all_lines.append('\t\t\t\t\t<h3 class="tag">skills</h3>')
    for skill in data['skills']:
        all_lines.append(f'\t\t\t\t\t<p>{skill}</p>')
    all_lines.append('\t\t\t\t</li>')

    # Activities
    all_lines.append('\t\t\t\t<li>')
    all_lines.append('\t\t\t\t\t<h3 class="tag">activities</h3>')
    all_lines.append(f'\t\t\t\t\t<p>{data["activities"]}</p>')
    all_lines.append('\t\t\t\t</li>')

    # Get to know me
    all_lines.append('\t\t\t\t<li>')
    all_lines.append('\t\t\t\t\t<h3 class="tag">get to know me</h3>')
    all_lines.append('\t\t\t\t\t<h4>Gets Me Up In The Morning</h4>')
    all_lines.append('\t\t\t\t\t<p>')
    all_lines.append(f'\t\t\t\t\t\t{data["morning"]}')
    all_lines.append('\t\t\t\t\t</p>')
    all_lines.append('\t\t\t\t</li>')

    return '\n'.join(all_lines)


def update_html(resume_html):
    """Replace the resume <ol> content in index.html."""
    html = read_file(HTML_PATH)

    ol_pattern = re.compile(
        r'(<ol class="resume-list">)\s*\n(.*?)\n(\s*</ol>)',
        re.DOTALL,
    )

    match = ol_pattern.search(html)
    if not match:
        print("ERROR: Could not find <ol class='resume-list'> in index.html")
        sys.exit(1)

    new_html = (
        html[:match.start()]
        + match.group(1) + '\n'
        + resume_html + '\n'
        + match.group(3)
        + html[match.end():]
    )

    write_file(HTML_PATH, new_html)
    print("\nSuccessfully updated index.html")


def main():
    data = parse_md()

    # Debug output for verification
    print("=== Parsed Resume Data ===")
    print(f"\nSkills ({len(data['skills'])}):")
    for s in data['skills']:
        print(f"  - {s}")

    print(f"\nActivities: {data['activities']}")
    print(f"\nMorning: {data['morning']}")

    print(f"\nEducation ({len(data['education'])} entries):")
    for e in data['education']:
        print(f"  [{e['title']}] — [{e['subtitle']}]")
        print(f"    Body: {e['body'][:100]}{'...' if len(e['body']) > 100 else ''}")

    print(f"\nExperience ({len(data['experience'])} entries):")
    for e in data['experience']:
        print(f"  [{e['title']}] — [{e['subtitle']}]")
        print(f"    Body: {e['body'][:100]}{'...' if len(e['body']) > 100 else ''}")

    resume_html = generate_resume_html(data)
    print("\n=== Generated HTML ===")
    print(resume_html)

    update_html(resume_html)


if __name__ == '__main__':
    main()
