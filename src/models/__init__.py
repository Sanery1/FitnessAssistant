"""
Data models for Fitness AI Assistant
"""
from .user import User, UserProfile, FitnessGoal, FitnessLevel, Gender
from .workout import WorkoutPlan, WorkoutSession, Exercise, ExerciseSet, MuscleGroup, ExerciseType, Difficulty
from .nutrition import NutritionPlan, Meal, FoodItem, MealType
from .body import BodyData, BodyComposition, BodyMeasurements
from .progress import ProgressRecord, ProgressSnapshot

__all__ = [
    "User", "UserProfile", "FitnessGoal", "FitnessLevel", "Gender",
    "WorkoutPlan", "WorkoutSession", "Exercise", "ExerciseSet", "MuscleGroup", "ExerciseType", "Difficulty",
    "NutritionPlan", "Meal", "FoodItem", "MealType",
    "BodyData", "BodyComposition", "BodyMeasurements",
    "ProgressRecord", "ProgressSnapshot",
]
