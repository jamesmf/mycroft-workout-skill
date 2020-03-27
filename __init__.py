from mycroft import MycroftSkill, intent_file_handler
import time
import json
from typing import List


class Exercise:
    def __init__(
        self, name: str, length: int, switch: bool = False, beep_every: int = 0
    ):
        self.name = name
        self.length = length
        self.switch = switch
        self.beep_every = beep_every


class WorkoutTimer(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)
        self.in_workout: bool = False

    def initialize(self):
        self.settings_change_callback = self.handle_settings
        self.handle_settings()

    def handle_settings(self):
        """
        Handles setting the necessary attributes on our object given
        the values in `settings`. Also runs when settings get updated.
        """
        ex: str = self.settings.get("exercise_list", "")
        self.log.info(ex)
        self.exercises = self.parse_exercises(ex)
        self.rest_len = self.settings.get("rest_len")

    def parse_exercises(self, ex_str: str) -> List[Exercise]:
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
        """
        If we get a stop command in the middle of a workout, we need a way
        to stop. Setting `self.in_workout = False` will cause the skill to
        stop the workout the next time the skill wakes.
        """
        self.in_workout = False

    def run_workout(self):
        """
        Iterate through the skill's exercises. If `self.in_workout` becomes
        False during the workout, we abort. If there is a specified `rest_len`
        then we also rest between each exercise.
        """
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
        """
        Mycroft walks you through your workout by telling you to begin the next
        exercise, optionally giving you time feedback, then telling you when
        that exercise is over. Since TTS takes time, the timing feedback can
        get out of sync. The skill measures elapsed time, so that issue should
        not compound (each exercise should only last its `length` plus the
        time it took for Mycroft to speak the next exercise/rest).
        """
        self.speak("begin {}".format(exercise.name))
        # keep track of elapsed time
        start = time.time()
        for n in range(0, exercise.length):
            # if it's a two-sided exercise, switch halfway through
            if exercise.switch and n == exercise.length // 2:
                self.speak("switch sides")
            elif n > 0 and exercise.beep_every > 0 and n % exercise.beep_every == 0:
                # if we're keeping track of time, provide time feedback
                self.beep()
            # if we get a `stop` command, end the exercise
            if not self.in_workout:
                return
            # check back in every second to see if we should stop and to
            # sync up elapsed time with sleep time.
            elapsed = time.time() - start
            sleeptime = n + 1 - elapsed
            if n + 1 - elapsed < 0:
                sleeptime += 1
                n += 1
            time.sleep(sleeptime)

    def beep(self):
        """
        # todo: better timing feedback. Possibly play a short, ticking sound.
        """
        self.speak("do")


def create_skill():
    return WorkoutTimer()
