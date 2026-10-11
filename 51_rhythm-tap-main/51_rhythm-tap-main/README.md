# Rhythm Tap

A 4-lane rhythm game — tap the right key as notes reach the hit line.

## Setup

```bash
pip install -r requirements.txt
python main.py
```

## Controls

| Key | Lane |
|-----|------|
| D | Lane 1 |
| F | Lane 2 |
| J | Lane 3 |
| K | Lane 4 |
| R | Restart |

## Tasks to Complete

### Task 1: Sound Effects on Hit
> Play a short beep or drum sound on each PERFECT, GREAT, or OK hit.



### Task 2: Hold Notes
> Add a long note type that the player must hold for 1 second to score.



### Task 3: BPM-Synced Spawning
> Notes should spawn on exact beats of a given BPM (e.g., 120 BPM) instead of a timer.


### Task 4: Grade Summary Screen
> After game over, show a breakdown: PERFECT count, GREAT count, OK count, MISS count, accuracy %.



## Folder Structure

```
rhythm-tap/
├── main.py
├── requirements.txt
├── game/
│   ├── __init__.py
│   ├── game_engine.py
│   └── beat.py
└── README.md
```

## Submission Checklist

Submission is only the following three things:

- [] A 10-second video of gameplay **before** your changes, showing the bug/broken behavior
- [] A 10-second video of gameplay **after** your changes, showing the bug fixed and the new features working
- [] The Chat/LLM used page link, with the complete chat history

