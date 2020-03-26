from mycroft import MycroftSkill, intent_file_handler


class WorkoutTimer(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

    @intent_file_handler('timer.workout.intent')
    def handle_timer_workout(self, message):
        self.speak_dialog('timer.workout')


def create_skill():
    return WorkoutTimer()

