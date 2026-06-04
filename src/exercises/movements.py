from src.exercises.base_exercise import BaseExercise, Phase


class Squat(BaseExercise):
    """
    Classic squat with tolerant thresholds.
    Uses knee angle for repetition counting.
    Avoids shoulder-angle checks because arm movement causes false warnings.
    """

    T_REST = 160
    T_PEAK = 112

    def _detect_phase(self, angles):
        knee_r = angles.get("knee_r", 180)
        knee_l = angles.get("knee_l", 180)
        knee = self.avg(knee_r, knee_l)

        if knee >= self.T_REST:
            return Phase.REST
        if knee <= self.T_PEAK:
            return Phase.PEAK
        if self._phase in (Phase.REST, Phase.ACTIVE):
            return Phase.ACTIVE
        return Phase.RETURN

    def _check_form(self, angles, phase):
        warn, err = [], []

        knee_r = angles.get("knee_r", 180)
        knee_l = angles.get("knee_l", 180)
        knee = self.avg(knee_r, knee_l)
        hip = self.avg(angles.get("hip_r", 180), angles.get("hip_l", 180))

        if abs(knee_r - knee_l) > 25:
            warn.append("Try to keep both knees moving evenly.")

        if phase == Phase.PEAK:
            if knee < 55:
                warn.append("Do not squat too deep. Keep the movement controlled.")

            if hip < 45:
                err.append("Keep your chest up and avoid folding forward.")

        return warn, err


class BicepCurl(BaseExercise):
    """
    Classic Bicep Curl.
    """

    T_REST = 155
    T_PEAK = 55

    def _detect_phase(self, angles):
        elbow = min(angles.get("elbow_r", 180), angles.get("elbow_l", 180))
        if elbow >= self.T_REST:
            return Phase.REST
        if elbow <= self.T_PEAK:
            return Phase.PEAK
        if self._phase in (Phase.REST, Phase.ACTIVE):
            return Phase.ACTIVE
        return Phase.RETURN

    def _check_form(self, angles, phase):
        warn, err = [], []
        shoulder_r = angles.get("shoulder_r", 90)
        shoulder_l = angles.get("shoulder_l", 90)

        if shoulder_r < 50 or shoulder_l < 50:
            err.append("Keep your elbows stable, do not use your shoulders!")
        if phase == Phase.PEAK:
            elbow = min(angles.get("elbow_r", 180), angles.get("elbow_l", 180))
            if elbow > 70:
                warn.append("Squeeze more at the top and hold!")
        return warn, err


class ShoulderPress(BaseExercise):
    """
    Overhead Shoulder Press.
    """

    T_REST = 70
    T_PEAK = 160

    def _detect_phase(self, angles):
        shoulder = self.avg(angles.get("shoulder_r", 90), angles.get("shoulder_l", 90))
        if shoulder <= self.T_REST:
            return Phase.REST
        if shoulder >= self.T_PEAK:
            return Phase.PEAK
        if self._phase in (Phase.REST, Phase.ACTIVE):
            return Phase.ACTIVE
        return Phase.RETURN

    def _check_form(self, angles, phase):
        warn, err = [], []
        hip = self.avg(angles.get("hip_r", 160), angles.get("hip_l", 160))
        if hip < 140:
            err.append("Do not hyperextend your lower back, keep your torso upright!")
        if phase == Phase.PEAK:
            elbow = self.avg(angles.get("elbow_r", 180), angles.get("elbow_l", 180))
            if elbow < 155:
                warn.append("Extend your arms fully!")
        return warn, err


class LateralRaise(BaseExercise):
    """
    Dumbbell Lateral Raise.
    """

    T_REST = 20
    T_PEAK = 70

    def _detect_phase(self, angles):
        shoulder = self.avg(angles.get("shoulder_r", 10), angles.get("shoulder_l", 10))
        if shoulder <= self.T_REST:
            return Phase.REST
        if shoulder >= self.T_PEAK:
            return Phase.PEAK
        if self._phase in (Phase.REST, Phase.ACTIVE):
            return Phase.ACTIVE
        return Phase.RETURN

    def _check_form(self, angles, phase):
        warn, err = [], []
        elbow_r = angles.get("elbow_r", 180)
        elbow_l = angles.get("elbow_l", 180)
        if elbow_r < 150 or elbow_l < 150:
            warn.append("Slightly bend your elbows, do not keep them completely locked or overly bent.")
        if phase == Phase.PEAK:
            shoulder = self.avg(angles.get("shoulder_r", 10), angles.get("shoulder_l", 10))
            if shoulder > 100:
                err.append("Do not go too high, stop at shoulder level!")
        return warn, err


class Lunge(BaseExercise):
    """
    Forward or Reverse Lunge.
    Uses the more bent knee to detect the lunge phase.
    """

    T_REST = 155
    T_PEAK = 100

    def _detect_phase(self, angles):
        knee = min(
            angles.get("knee_r", 180),
            angles.get("knee_l", 180)
        )

        if knee >= self.T_REST:
            return Phase.REST
        if knee <= self.T_PEAK:
            return Phase.PEAK
        if self._phase in (Phase.REST, Phase.ACTIVE):
            return Phase.ACTIVE
        return Phase.RETURN

    def _check_form(self, angles, phase):
        warn, err = [], []

        if phase == Phase.PEAK:
            hip = self.avg(
                angles.get("hip_r", 160),
                angles.get("hip_l", 160)
            )

            front_knee = min(
                angles.get("knee_r", 180),
                angles.get("knee_l", 180)
            )

            back_knee = max(
                angles.get("knee_r", 180),
                angles.get("knee_l", 180)
            )

            if hip < 130:
                err.append("Keep your upper body upright.")

            if back_knee > 120:
                warn.append("Bring your back knee closer to the ground.")

            if front_knee < 65:
                warn.append("Do not bend your front knee too much.")

        return warn, err


class TricepExtension(BaseExercise):
    """
    Overhead Tricep Extension.
    """

    T_REST = 80
    T_PEAK = 155

    def _detect_phase(self, angles):
        elbow = self.avg(angles.get("elbow_r", 90), angles.get("elbow_l", 90))
        if elbow <= self.T_REST:
            return Phase.REST
        if elbow >= self.T_PEAK:
            return Phase.PEAK
        if self._phase in (Phase.REST, Phase.ACTIVE):
            return Phase.ACTIVE
        return Phase.RETURN

    def _check_form(self, angles, phase):
        warn, err = [], []
        shoulder = self.avg(angles.get("shoulder_r", 160), angles.get("shoulder_l", 160))
        if shoulder < 140:
            err.append("Keep your upper arm vertical, your elbows shouldn't move forward/backward!")
        if phase == Phase.PEAK:
            elbow = self.avg(angles.get("elbow_r", 90), angles.get("elbow_l", 90))
            if elbow < 150:
                warn.append("Extend your arm fully!")
        return warn, err


class PushUp(BaseExercise):
    """
    Classic Push-Up.
    """

    T_REST = 155
    T_PEAK = 100

    def _detect_phase(self, angles):
        elbow = self.avg(angles.get("elbow_r", 180), angles.get("elbow_l", 180))
        if elbow >= self.T_REST:
            return Phase.REST
        if elbow <= self.T_PEAK:
            return Phase.PEAK
        if self._phase in (Phase.REST, Phase.ACTIVE):
            return Phase.ACTIVE
        return Phase.RETURN

    def _check_form(self, angles, phase):
        warn, err = [], []
        hip = self.avg(angles.get("hip_r", 180), angles.get("hip_l", 180))
        if hip < 150:
            err.append("Do not raise your hips, maintain a straight body line!")
        if hip > 178:
            err.append("Your hips are sagging too low!")
        shoulder = self.avg(angles.get("shoulder_r", 90), angles.get("shoulder_l", 90))
        if shoulder > 60:
            warn.append("Keep your elbows close to your torso (tucked in).")
        return warn, err


class Deadlift(BaseExercise):
    """
    Conventional or Romanian Deadlift.
    """

    T_REST = 160
    T_PEAK = 95

    def _detect_phase(self, angles):
        hip = self.avg(angles.get("hip_r", 180), angles.get("hip_l", 180))
        if hip >= self.T_REST:
            return Phase.REST
        if hip <= self.T_PEAK:
            return Phase.PEAK
        if self._phase in (Phase.REST, Phase.ACTIVE):
            return Phase.ACTIVE
        return Phase.RETURN

    def _check_form(self, angles, phase):
        warn, err = [], []
        knee = self.avg(angles.get("knee_r", 175), angles.get("knee_l", 175))
        if knee < 140:
            warn.append("Knees are bent too much, make sure you are engaging your hamstrings.")

        shoulder_r = angles.get("shoulder_r", 90)
        shoulder_l = angles.get("shoulder_l", 90)
        if shoulder_r < 30 or shoulder_l < 30:
            err.append("Shoulders should not pass the bar line, keep your back flat!")

        if phase == Phase.PEAK:
            hip = self.avg(angles.get("hip_r", 180), angles.get("hip_l", 180))
            if hip < 70:
                warn.append("You might be leaning down too low, please check.")
        return warn, err


class Plank(BaseExercise):
    """
    Static Forearm Plank.
    """

    def _detect_phase(self, angles):
        return Phase.PEAK

    def _check_form(self, angles, phase):
        warn, err = [], []
        hip = self.avg(angles.get("hip_r", 180), angles.get("hip_l", 180))

        if hip < 155:
            err.append("Your hips are too high! Flatten your body.")
        elif hip > 175:
            warn.append("Your hips are too low, do not let your lower back sag.")

        shoulder = self.avg(angles.get("shoulder_r", 90), angles.get("shoulder_l", 90))
        if shoulder < 70 or shoulder > 110:
            warn.append("Shoulders should be directly above your elbows.")

        return warn, err

    def _tick_counter(self, new_phase, has_error):
        return False


class BentOverRow(BaseExercise):
    """
    Bent Over Row.
    """
    
    T_REST = 150
    T_PEAK = 70

    def _detect_phase(self, angles):
        elbow = self.avg(angles.get("elbow_r", 180), angles.get("elbow_l", 180))
        if elbow >= self.T_REST:
            return Phase.REST
        if elbow <= self.T_PEAK:
            return Phase.PEAK
        if self._phase in (Phase.REST, Phase.ACTIVE):
            return Phase.ACTIVE
        return Phase.RETURN

    def _check_form(self, angles, phase):
        warn, err = [], []
        hip = self.avg(angles.get("hip_r", 180), angles.get("hip_l", 180))
        if hip > 140:
            err.append("Keep your torso bent forward, do not stand up straight!")
        if phase == Phase.PEAK:
            shoulder = self.avg(angles.get("shoulder_r", 90), angles.get("shoulder_l", 90))
            if shoulder > 50:
                warn.append("Drive your elbows back and squeeze your shoulder blades.")
        return warn, err


class CalfRaise(BaseExercise):
    """
    Standing Calf Raise.
    """

    T_REST   = 155
    T_PEAK   = 170  

    def _detect_phase(self, angles):
        knee = self.avg(angles.get("knee_r", 165), angles.get("knee_l", 165))
        if knee <= self.T_REST:
            return Phase.REST
        if knee >= self.T_PEAK:
            return Phase.PEAK
        if self._phase in (Phase.REST, Phase.ACTIVE):
            return Phase.ACTIVE
        return Phase.RETURN

    def _check_form(self, angles, phase):
        warn, err = [], []
        hip = self.avg(angles.get("hip_r", 175), angles.get("hip_l", 175))
        if hip < 155:
            err.append("Keep your body upright, do not lean forward!")
        if phase == Phase.PEAK:
            shoulder = self.avg(angles.get("shoulder_r", 10), angles.get("shoulder_l", 10))
            if shoulder > 30:
                warn.append("Keep your arms stable, do not swing them.")
        return warn, err


class FrontRaise(BaseExercise):
    """
    Dumbbell Front Raise.
    """

    T_REST = 20
    T_PEAK = 75

    def _detect_phase(self, angles):
        shoulder = self.avg(angles.get("shoulder_r", 10), angles.get("shoulder_l", 10))
        if shoulder <= self.T_REST:
            return Phase.REST
        if shoulder >= self.T_PEAK:
            return Phase.PEAK
        if self._phase in (Phase.REST, Phase.ACTIVE):
            return Phase.ACTIVE
        return Phase.RETURN

    def _check_form(self, angles, phase):
        warn, err = [], []
        elbow = self.avg(angles.get("elbow_r", 175), angles.get("elbow_l", 175))
        if elbow < 150:
            warn.append("Arms should be nearly straight, do not bend them too much.")
        if phase == Phase.PEAK:
            shoulder = self.avg(angles.get("shoulder_r", 10), angles.get("shoulder_l", 10))
            if shoulder > 100:
                err.append("Do not raise your arms above shoulder level, risk of strain!")
        return warn, err


EXERCISE_REGISTRY: dict[str, type] = {
    "squat":            Squat,
    "bicep_curl":       BicepCurl,
    "shoulder_press":   ShoulderPress,
    "lateral_raise":    LateralRaise,
    "lunge":            Lunge,
    "tricep_extension": TricepExtension,
    "push_up":          PushUp,
    "deadlift":         Deadlift,
    "plank":            Plank,
    "bent_over_row":    BentOverRow,
    "calf_raise":       CalfRaise,
    "front_raise":      FrontRaise,
}


def get_exercise(name: str) -> BaseExercise:
    key = name.lower().replace(" ", "_")
    cls = EXERCISE_REGISTRY.get(key)
    if cls is None:
        raise ValueError(f"Unknown exercise: '{name}'. "
                         f"Available options: {list(EXERCISE_REGISTRY)}")
    return cls()