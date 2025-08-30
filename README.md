# 🎮 Game of Power of 10

## 🔗 Live Demo  
**Coming soon...**  

## 👨‍💻 Development Team
- **Zhong Yi Yan** — Full Stack Developer / AI Developer

---

## 📝 Description
**Game of Power of 10** is a competitive math-based card game for two players, redesigned with modern technologies. This new version is a complete remodel of the original [Game of 10](https://github.com/LucaYan0506/Game-of-10), now built with **React** on the frontend and **Django** on the backend — replacing the previous HTML/CSS approach.

---

## 🚀 Features

### 🎮 Game Modes
- **Standard Mode** with a complete core game structure
- **Game of X Mode** (Upcoming) supporting both:
  - Player vs Player (PvP)
  - Player vs AI
- **Hard Mode** (Upcoming) for increased challenge, also available in both PvP and AI modes

### 🤖 AI Engine (Upcoming)
- AI opponents using:
  - **Deep Q-Learning**
  - **Monte Carlo Tree Search (MCTS)**
  - **Brute Force** logic (prioritizes moves when available; otherwise discards)

### 📊 Game Statistics (Upcoming)
- Track number of games won/lost
- Total games played (PvP and against AI)
---

## 🎮 Game Modes

### Standard Mode

Game of Power of 10 is a math-based competitive card game for 2 players.
Each player starts with 6 cards:

* 🟦 4 number cards
* ➕ 2 operation cards (e.g., +, −, ×, ÷)

#### 🎯 Objective

Create an equation that results in a power of 10 (e.g., 10, 100, 1000, …).

#### 🧮 Scoring

* ✅ +1 point for each operation used
* ✅ +1 bonus point if all 4 numbers are used
* 🏆 First player to reach 20 points wins

#### 🔁 Gameplay

* Use as many cards as possible to form a valid equation equal to a power of 10
* Equations can be formed horizontally or vertically
* You may reuse cards already placed on the table
* If stuck, discard one card and draw a new one

---

### Expansion Mode

This variant rewards **longer equations** by giving bonus points based on board usage.

#### 🧮 Scoring

* ✅ Same as *Standard Mode*
* ➕ +0.5 points for each board cell used in the equation

*(Example: if your equation uses 8 cells, you earn 4 bonus points on top of standard scoring.)*

---

### 📊 Mode Comparison

| Rule / Feature    | Standard Mode                | Expansion Mode                                          |
| ----------------- | ---------------------------- | ------------------------------------------------------- |
| Base points       | +1 per operation             | +1 per operation                                        |
| Full-hand bonus   | +1 if all 4 numbers are used | +1 if all 4 numbers are used                            |
| Extra board usage | –                            | +0.5 points per board cell used                         |
| Win condition     | First to 20 points           | First to 20 points (with bonus points speeding up play) |

---


## 🛠️ How to Play

### 🆕 Create a Match
- On the **Home Page**, click **"Create Match"**
- A unique **Game ID** will be generated for the match

### 👥 Join a Match
- Click **"Play"**
- Enter the **Game ID** provided by another player to join the match

---

## 🧪 Tech Stack
- **Frontend**: React (TypeScript)
- **Backend**: Django (Python)


---

<!-- ## 📷 Screenshots 
> _Coming soon..._  
Add gameplay screenshots or GIFs here when available -->

---

## 🤝 Contributing
Currently, this is a solo project. In the future, contributions may be welcome — stay tuned!


