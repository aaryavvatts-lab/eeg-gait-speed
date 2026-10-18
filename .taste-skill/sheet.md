# DIRECTION SHEET — The contact sheet
seed 510588348 · drawn 2026-10-18 · sector health
Brief: Reading walking speed from the scalp: EEG and leg muscle recordings from 58 people walking at three speeds drive a simulated wheelchair speed control; the random split scored 92 percent and the honest split 53

| | |
| --- | --- |
| Direction | The contact sheet |
| Hero | Lit strip, four corners |
| Type | kept from the brand |
| Colour | kept from the brand |
| Sections | intro (Narrow column, empty field) → showcase (Frame run, one lifted) → how-it-works (Drag row of moments) → stats (Column aligned on the decimal) → list (Two-ended rows, narrow column) → footer (A single quiet line) |
| Motion | Drag row |
| Photographs | the "Fog and quiet" set, as atmosphere |

This is the direction for this build. Adopt it. Do not blend it with the layout you would have made anyway,
and do not redraw because it is unfamiliar: unfamiliar is the point. Redraw a slot only when it conflicts
with a stated brand constraint or needs an asset that does not exist, and say why in your report.

The parts of this sheet were written separately and will disagree in small ways. Settle every disagreement in this order:
**house rules** (including type no smaller than 13px and body text of 16px or more) → **the direction** (the idea, the composition habits, where the
one accent goes) → **the type system and the palette** (which face does which job, the five size steps, which colour is the ground and where the
accent goes) → **the hero blueprint** → **the section blueprints**. Under each blueprint below, "Adjusted for this page" lists where it disagrees.
In practice: take geometry from blueprints (columns, proportions, what sits where) and take everything else from above them. Map every size a
blueprint names onto one of your five type steps instead of adding a sixth. Use one button shape, one corner radius and one pair of page margins on
the whole page, whatever individual blueprints say. If a blueprint names a kind of typeface (a light serif, a heavy grotesk), use the dealt face.

## 1. The idea
Show everything at once, small, in order. The work is laid out like a photographer's contact sheet or an archive drawer: dozens of small frames in strict rows, with all text set at one small size. Nothing is featured, which is the point: the volume and consistency of the body of work is the statement, and the visitor does the choosing. It suits people and studios whose strength is range and output.

Before anything else, write one sentence in your notes: "On this page, <the subject's own material> becomes <the device>."
Fill the first blank from your inventory of what only this client has (its name and what it means, its street, its numbers, its
constraint), then put the nearest competitor in the sentence: if it still works, the idea is the category's, not the client's.
Then name the one live thing the visitor can do on the page (SKILL.md step 4).

## 2. Composition
The name, or one sentence about the work, sits at display size (6–9vw) across the top of the first screen, and the sheet begins directly under it, still inside the first screen. The first screen opens with three or four short blocks of small text across the top on a 12-column grid (who, what, where to reach them), all at 14–16px, and immediately below, the sheet begins: rows of thumbnails at a fixed height (90–140px) with their natural widths, 6–10px gaps, each project forming a run of four to eight frames preceded by its title in the same small text. The sheet fills the whole page width edge to edge with 16–20px margins. Hovering a run dims the others and shows that project's one-line description in a fixed position. A single enlarged frame may interrupt the sheet once per screen at four times the size.

## 3. Type
Kept from the brand. One face. The name at display size on the first screen; everything else at one text size and one small size; hierarchy below the name comes from position and from a single brighter ink for titles.

## 4. Colour
Kept from the brand. Black or white ground, so the thumbnails are the only colour.

## 5. Imagery
**The project has no photographs of its own yet.** First choice: **real pictures of the subject's world from the open collections**: its city and street in old postcards and photographs, an old map of the neighbourhood, its materials up close, its trade in engravings, museum objects of its kind (references/imagery.md §3). Start with `node /Users/aaryav-sharma/.claude/skills/design-taste-frontend/scripts/assets.mjs "speed control"`, then queries from your inventory (its street, its materials, its trade's tools and history). Download what you use into the project with `--get` and credit every one on the page (`--credits` prints the footer line). They show the world around the client, never the client's own room, dish, product, person or team. Second, for what no honest picture exists of: draw the subject's own things in code, large, in one flat graphic language and the palette's real colours (its tiles, its windows, its objects; references/imagery.md §8). Third: the dealt photographs, only where an honestly generic picture fits (the sea, the weather, a material), never one a visitor could take for the thing itself and never an unrelated scene. One treatment for all of them. If this direction is built on photographs, plan the set before building (four to six pictures of one family) and reuse them at different crops and scales instead of finding or drawing a new picture for every slot; keep drawings as `<symbol>` + `<use>` or generate them with a small script so the page stays light. List every found picture (with its source and licence), every dealt photograph and every drawing that stands in for photography in your report.

Many images: at least 24 frames to make a sheet. They can be project photographs from the dealt set cropped to mixed ratios, or page captures of the work. Square corners, no captions on the frames.

**Floor (the inspector checks it):** at least four real pictures on the page, usually six to twelve; SVG drawings do not count. One moving picture where an honest clip exists: `node <skill>/scripts/assets.mjs --video "<query>"`, used as a muted loop with a poster frame. Whatever this direction says about pictures, it is carried out with real ones.

Photographs dealt for this build, from the "Fog and quiet" set (misty, muted, minimal landscapes and empty horizons; calm areas for text)
Order of preference for imagery: (1) the project's own photographs and product shots; (2) images you generate, if an image tool is
available; (3) real pictures of the subject's world found in the open collections (assets.mjs, downloaded and credited on the page);
(4) drawings of the subject in code; (5) these. They are real photographs (Unsplash licence, served by picsum.photos) of places, light and
texture. They are atmosphere, never a stand-in for a specific product, dish, person or interface. List the ones you use in your report so
they can be replaced.
- `https://picsum.photos/id/266/1600/1000` — Three ships on a distant horizon across a calm blue sea · mid tone · pale blue, deep blue · calm area: all · native landscape · photo: John Maravelakis
- `https://picsum.photos/id/70/1600/1000` — Road lined with tall trees fading into thick fog · mid tone · grey, dark green · calm area: centre · native landscape · photo: Dorothy Lin
- `https://picsum.photos/id/544/1600/1000` — Layered hill ridges fading into warm beige mist · mid tone · beige, warm brown, cream · calm area: top · native landscape · photo: Francesco Gallarotti
- `https://picsum.photos/id/269/1600/1000` — Gulls perched on a concrete wall beside a pale still sea · light tone · white, pale blue, grey · calm area: left · native landscape · photo: Jill Heyer
- `https://picsum.photos/id/353/1600/1000` — Low cloud drifting over dark green forested hills · dark tone · deep green, grey · calm area: top · native landscape · photo: Forrest Cavale
- `https://picsum.photos/id/634/1600/1000` — Pine forest dissolving into fog beneath a pale pink sky · mid tone · dark green, pale pink, white · calm area: top · native landscape · photo: Jay Mantri
- `https://picsum.photos/id/172/1600/1000` — Stone jetty stretching into still water and dense grey fog · mid tone · grey, warm grey · calm area: top · native landscape · photo: Aleksi Tappura
- `https://picsum.photos/id/552/1600/1000` — Tiny sailboat on a calm sea with distant hills, black and white · mid tone · grey, white, black · black-and-white · calm area: all · native landscape · photo: Hugo Kerr
The last two path numbers are width and height: request the exact crop you render (`/1200/1500` for a 4:5 portrait, `/2400/1350` for a hero) and
add `?grayscale` to desaturate. Use three to six of them, not all eight. Always set `width`, `height`, `alt` and `loading="lazy"` (not on the hero image).
Other sets that fit this brief: people, interior-and-table, animals, coast — `node draw.mjs --photos <set>` prints one in full; `--photos list` shows all sets. Taking photographs from another set is your call and is not a redraw; keep them to one light and one treatment.

## 6. Hero — Lit strip, four corners
One near-black field with a single lit band. Four small pieces of text at 14px, medium weight, sit in the corners on 72px side margins and 44px top and bottom margins: the name top-left, one link top-right, one sentence saying what this is bottom-left (max 36ch), the single action as a text link bottom-right. Across the vertical middle runs one horizontal strip of photographs, 34vh tall (about 300px), each at its natural width with 10px gaps and square corners: eleven or more frames in a flex row wider than the viewport, so the first and last visible frames are cropped by the left and right edges. The frame nearest the centre is at full brightness; the others sit at filter: brightness(0.55) and brighten on hover or as they reach the centre. Under the centred frame, aligned to its left edge, its title is set in the same 14px text. The top quarter and the bottom quarter of the screen stay empty and dark. The strip scrolls sideways with overflow-x: auto and scroll-snap; never hijack vertical scroll.

On a phone: The strip stays a single sideways-scrolling row but grows to 46vh tall, so one frame and the cropped edges of its neighbours fill the width. The name and the link sit at the top on 20px margins; the sentence and the action stack bottom-left under the strip at 14px. Dark space remains above and below the strip, about 12% of the height each.
Headline: None at display size: the name at 14px in a corner and one sentence of up to 60 characters.

Adjusted for this page:
- It sets running text at 14px: paragraphs use your body step (16px or more).
- It names colours (black): map them onto this palette's roles (ground `--bg`, panels `--surface` and the fields, text `--ink`/`--muted`, the accent `--accent` on the primary action only).
- Its action is a text link: the primary action on the first screen is a real button (filled or solid-bordered, 44px or taller), placed where the blueprint puts the link. A second action may stay a link.

## 7. Sections, in order
Each is a composition to rebuild with this project's content. Keep the geometry; change the subject. Re-order or drop a
section when the argument of the page needs it (see references/copy.md), never to fall back to a card grid.

### 1. intro — Narrow column, empty field (stack)
A single text column 300–340px wide, its left edge at 15% of the viewport width, starting 64px below the section top. It holds four or five short paragraphs at 15–16px with leading 1.5 and one blank line between them; the first paragraph is in medium weight and full ink, the rest in regular weight and the soft ink. No heading, no image, no button; one underlined text link may end the last paragraph. The remaining three-quarters of the 1440 screen is untouched ground, and the section is only as tall as the text plus 160px of padding below. The column's left edge must match a line used elsewhere on the page (the wordmark's left edge or a later column). Where the page has a large object or a fixed photograph, this column is the small text beside it. Holds 90–150 words comfortably.
On a phone: The column becomes 78% of the width, left-aligned at the 20px margin, so a strip of empty ground remains on the right as a deliberate margin. Text stays at 15–16px with the first paragraph in medium weight. Padding is 72px above and 96px below.

### 2. showcase — Frame run, one lifted (strip)
Columns 1–3 are a nearly empty column: the heading (two to four words at 24–28px) at the top, a link under it, and one or two short notes at 15px much further down, each level with the frame it describes. Columns 4–12 hold a run of six to eight frames of the same subject at one fixed height of 30vh, with natural widths and 6px gaps: the whole view, a tight crop of the same thing, a detail, the reverse side. The run is allowed to leave the right edge. One frame is lifted out of the row: shown at 2.2 times the row height with its bottom aligned to the row's bottom (flex row, align-items: end), so it stands above the others. Under each frame, at 15px: a name on the left and a single fact on the right. Square corners, no captions on the images.
On a phone: The heading and link sit on top. The lifted frame comes first at full width. The rest of the run scrolls sideways beneath it at a fixed height of 34vw with 4px gaps and scroll-snap, bleeding off the right edge. Notes are listed under the run at 15px.

### 3. how-it-works — Drag row of moments (carousel)
A story told left to right. Top row: the heading, two to four words at 28–36px, at the left margin; at the right margin two solid square buttons, 48px each, for back and forward. Directly beneath, a solid bar 6px tall spans the full width in a soft tone, with a full-ink segment showing how far the row has been scrolled. Then the row itself: six to nine columns, each 280px wide with 32px gaps, in a horizontally scrolling flex container with scroll-snap that bleeds off both viewport edges. Every column reads top to bottom: a one-line caption at 18px bold that carries the order in words ('We met', 'Two winters on', 'The move'), three lines at 15px in the soft ink, then 80–140px of empty space that varies per column, then a 4:5 portrait photograph. Because the spaces vary, the photographs' top edges rise and fall along the row.
On a phone: Columns are 72vw wide with 16px gaps, so the next one always shows at the right edge. The buttons are dropped; the 6px progress bar stays under the heading. The empty space inside columns shrinks to 32–64px but still varies from column to column.

### 4. stats — Column aligned on the decimal (table)
A tall column of figures set like a ledger. Left, columns 1–5: the heading as a statement of up to five words on two lines at clamp(32px, 3.2vw, 52px), its first line in the soft ink and its second in full ink, placed at mid-height. Right, columns 7–12: four to six figures stacked, each at clamp(64px, 7vw, 112px), leading 1.0, in tabular lining numerals. They align on the decimal point: each row is a three-part grid in which the whole-number part is right-aligned in the first track, the point and decimals are left-aligned in the second, and a caption of one or two lines at 16px sits in the third, on the figure's baseline. Whole numbers simply leave the second track empty. Rows are separated by 20px of space only. Units are written in the captions, not attached to the figures, so the numerals form one clean vertical shape.
On a phone: The heading comes first at 28px. Figures drop to 15vw and keep the decimal alignment, with the split at 52% of the width. Each caption moves under its figure at 15px, starting from the left margin. 28px between rows.

Adjusted for this page:
- It sets a sentence large over several lines: jurors read that as a long headline. Either cut it to a two-line headline at display size, or keep it a statement at 36px or less on three lines (24px, four lines on a phone).

### 5. list — Two-ended rows, narrow column (list)
A list in one narrow column, 520px wide, starting at 22% of the viewport width or centred. Every row is 34–38px tall with no box and nothing drawn between rows. Each row has two ends: at the left, a 16px round image (a face, a logo, a colour dot) followed after 8px by the name at 15–16px in full ink; at the far right of the column, a short value at 13px in the soft ink (a date, a price, a domain, an opening time) with tabular figures. Entries that need a sentence run to two lines at the left, and the value aligns with the first line. Groups are separated by 40px of space and begin with one plain word in the soft ink at the same size. A heading of two to four words at 24–28px in medium weight sits 32px above the first row. Holds 10–40 rows.
On a phone: The column fills the width with 20px margins. Rows are 44px tall for touch; the left image stays 16px. Long values wrap beneath the name at 13px, left-aligned with it, and the row grows. Group spacing is 32px.

### 6. footer — A single quiet line (strip)
No footer block at all. After at least 30svh of empty page ground, one baseline 30px above the bottom edge carries three items in the page's ordinary small text size (14–16px), the same size and weight as the navigation: at the left margin, what this is in three or four words; centred, two to five links separated by 24px of space; at the right margin, the year and a privacy link. Use a three-column grid (1fr auto 1fr) so the centre group is truly centred whatever the side lengths. No logo, no background change, no line above it, no columns. Links are in the full ink; the rest in the softer ink. If the page has a narrow text column, the three items may instead sit on that column's left edge as one wrapped line. The restraint only works if the page above has already made its invitation.
On a phone: Three short lines at 14px on the left margin with 8px between them: the description, the links on one wrapped line, then year and privacy. Links stay in the full ink. Leave 20svh of empty ground above and 24px below.

## 8. Motion — Drag row
A row of large items wider than the screen that the visitor pulls sideways: native horizontal scrolling with scroll snapping, the first item aligned to the page margin and the last allowed to run off the edge so the row visibly continues. No carousel library, no arrows, no dots.
This is the signature move, the one loud moment. Around it the page still needs the rest of the motion layer (SKILL.md step 9): an entrance for the parts of every section, feedback on every control, and one moving picture. The inspector fails a page that barely moves. Recipes: references/motion.md.

## 9. Where the richness comes from
Density and order. The mass of small images forms a texture; the strict rows keep it calm.

## 10. How this direction goes wrong
With fewer than about 20 images it looks unfinished; choose another direction. Do not add a big headline above the sheet. On a phone the frames become two per row at a fixed height and each run scrolls sideways. Rows that run past the right edge read as clipped in screenshots and to most visitors: wrap the frames onto the next line, or end each row inside the grid.

## 11. Real references
Studied sites that work this way. Take the principle, never the specifics: no names, copy, images or signature assets of theirs.
- **Gil Huybrecht** (Awwwards Site of the Day, studied score 7.6) `aww-gil-huybrecht`
  Idea: A portfolio as a contact sheet: every project is a numbered run of miniature page screenshots on black, and all text is set at one small size.
  Hero: Black field on a seven-column grid with 14px margins. The top band is plain white text at one size, about 16px: name in column one, availability in column two, a services list from column three, a longer awards list from column five, then 'Profile' and 'Email me' at the right. List items are indented one step under their label. Below the lists roughly 300px of black is left empty. At mid-height the thumbnail grid begins: one small website screenshot per column, about 190px wide, each topped by a number at its right corner, with the project name over the first of each run. Two tiny toggle chips sit in the bottom corners.
  Worth taking: Set every piece of text on the page at one size and weight and build hierarchy only from column position and a one-step indent under labels.
- **PROOOOF** (One Page Love, studied score 7.4) `opl-proooof`
  Idea: The product's output is the page: a wall of photos each wearing its coloured EXIF strip, with all the copy folded into one small floating card.
  Hero: The whole viewport is a six-column masonry of photographs on a warm off-white ground with about 15px gutters, columns offset vertically so rows never line up. Each photo has a flat strip fused to its bottom edge carrying tiny monospaced capture data, every strip a different solid colour (black, red, orange, yellow, violet, green). Dead centre floats a white card about 380px wide and 410px tall with roughly 28px corner radius and a soft shadow. It contains an extended wordmark with chained O's, a two-row accordion with the first row open, an App Store badge and a monospaced line of links. There is no navigation.
  Worth taking: Show the product's output at wall scale as the background and confine all copy to one small card on top of it.
- **Zara Webb** (One Page Love, studied score 8) `opl-zara-webb`
  Idea: A one-woman newborn-care practice presented like a hand-made keepsake: a mascot rabbit, scalloped and flower-shaped cut-outs, candid film photographs.
  Hero: Split exactly in half. Left, on cream: two-line mono caps nav stacks sit at the column's top-left and top-right with a handwritten script logo centred between them. Centred below, a five-line headline in a condensed serif, each line broken to one to three words so the block forms a ragged lozenge; then a three-line 16px sans paragraph and an outlined pill button in mono caps. A line-drawn rabbit on a skateboard rides a hairline at the column's bottom-right. Right: a candid flash photograph bleeds off the top and right edges and stops at 92% height; a lilac pill button and a round chat icon overlay its top-right corner.
  Worth taking: Mask photographs into soft custom shapes (a four-petal flower, a scalloped egg) and let their container crop them.
Full notes on any of them: `node draw.mjs --site <id>`.

## Always
Headlines two lines or fewer at every width. No eyebrow labels, no monospace, no 01/02/03, no thin rules, no gradients, no shadows at rest,
no cream-and-terracotta, no violet. `inspect.mjs` measures all of it.

Saved to /Users/aaryav-sharma/WheelChair EEG Data Set Insta Project/.taste-skill/direction.json · reprint with `node draw.mjs --show`
