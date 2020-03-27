from mycroft import MycroftSkill, intent_file_handler
import time
import json


class Exercise:
    def __init__(self, name, length, switch=False, beep_every=0):
        self.name = name
        self.length = length
        self.switch = switch
        self.beep_every = beep_every


class WorkoutTimer(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)
        self.in_workout = False

    def initialize(self):
        self.log.info(str(self.settings.get("exercises_json")))
        self.settings_change_callback = self.handle_settings
        self.handle_settings()

    def handle_settings(self):
        ex = self.settings.get("exercise_list", "")
        self.log.info(ex)
        self.exercises = self.parse_exercises(ex)
        self.rest_len = self.settings.get("rest_len")

    def parse_exercises(self, ex_str):
        """
        Parse a comma-delimited string of exercises in the format
          name | length | beep_every (optional) | switch (optional)
        into Exercise objects

        For example an exercise called "plank" that lasts 30 seconds,
        plays a beep every second, and tells you to switch sides halfway
        through looks like
          plank|30|1|switch
        while 30 seconds of crunches with no beeps and no switch looks like
          crunches|30||

        Combined, a 3-exercise workout might look like
         plank|30|1|switch,crunches|30||switch,push ups|30|15|
        """
        if ex_str.strip() == "":
            return []
        out = []
        split = ex_str.split(",")
        for ex in split:
            ex_sp = ex.split("|")
            d = {"name": ex_sp[0], "length": int(ex_sp[1])}
            try:
                d.update({"beep_every": int(ex_sp[2])})
                d.update({"switch": ex_sp[3] == "switch"})
            except (IndexError, ValueError):
                pass
            out.append(Exercise(**d))
        return out

    @intent_file_handler("timer.workout.intent")
    def handle_timer_workout(self, message):
        self.run_workout()

    def stop(self):
        self.in_workout = False

    def run_workout(self):
        self.in_workout = True
        for n, exercise in enumerate(self.exercises):
            self.run_exercise(exercise)
            if self.in_workout == False:
                return
            if n == len(self.exercises) - 1:
                self.speak("Workout completed! Good job.")
                return
            if self.rest_len > 0:
                self.run_exercise(Exercise("Rest", self.rest_len))

    def run_exercise(self, exercise):
        self.speak("begin {}".format(exercise.name))
        start = time.time()
        for n in range(0, exercise.length):
            if exercise.switch and n == exercise.length // 2:
                self.speak("switch")
            elif n > 0 and exercise.beep_every > 0 and n % exercise.beep_every == 0:
                self.beep()
            if self.in_workout == False:
                return
            elapsed = time.time() - start
            sleeptime = n + 1 - elapsed
            if n + 1 - elapsed < 0:
                sleeptime += 1
                n += 1
            self.log.info("n: {}, sleep: {}, elapsed: {}".format(n, sleeptime, elapsed))
            time.sleep(sleeptime)

    def beep(self):
        self.speak("do")


def create_skill():
    return WorkoutTimer()
