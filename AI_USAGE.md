# AI Usage Documentation

## Tools Used
- **Claude** for explaining best practices and project management
- Assistance with code review and debugging code
- Checking mistakes and putting me back on the right path.

## Key Prompts

1. "I get 'Access denied' / 'git is not recognized' / 'not a git repository'. What does
   it mean and how do I fix it?" 
2. What if I don't have or don't want to use my root password? Is there a way around that?
3. What reccomendations do you have for this assignement around CRUD routes and validation?
4. My code is incorrect but I don't know why (paste my code)	
 


## What Worked Well

- **Guidance:** Breaking work into small steps, with chance to confirm accuracy, made it easy to ensure my work was of a high caliber.
- **Boilerplate:** Claude  assisted in basic CRUD routes and validation, was a great boon in using/understanding parameterized queries (`%s` placeholders) throughout.
- **Reusing my coursework:** The Dashboard queries come from my Assignment 6 analytics queries, and the JSON columns from Assignment 7.
- **Explaining errors:** Claude explained error messages (Some examples: MySQL error 1045, Git
  identity errors, the wrong-folder `fatal: not a git repository`) in plain language.


## What I Changed or Decided (Modified)

- I wanted set up a way to acess without MySQL root password, so I created a separate `tracker_user`
  account limited to my databases. The app uses that account.
- I kept my Assignment 1-8 database (`job_tracker`) separate from the project database
  (`job_tracker_app`) so the project schema could follow the specifications exactly
- I tested each feature in the browser, including validation errors and the delete
  confirmations, and removed my test data before recording the demo.


## Lessons Learned

- AI is excellent for boilerplate and for explaining errors, but I still have to run
  and test everything. AI can also make mistakes and you have to be cognisiant of that.
- Reading Git's output carefully matters: the commit file list is how the leaked
  password was caught before it reached a public repo.
- Asking the AI to explain why a step works, not just "what to type", helped me
  understand transactions, indexes, foreign keys, and JSON queries in practice.
- Separating logic (`matching.py`) from the web layer makes it testable, and the unit
  tests gave me confidence in the Job Match percentages.
