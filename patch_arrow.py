with open("frontend/src/app/page.tsx", "r") as f:
    page = f.read()

page = page.replace("return `${workouts[0].date} ➡️ ${activePlan.race_date}`;", "return `${workouts[0].date} - ${activePlan.race_date}`;")

with open("frontend/src/app/page.tsx", "w") as f:
    f.write(page)
