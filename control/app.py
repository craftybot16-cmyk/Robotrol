import os

from control.config import load_all_configs
from control.pipeline import PickPlacePipeline
from control.robot import MockRobot
from control.gripper import MockGripper
from control.executor import TrajectoryExecutor
from perception.camera import build_camera
from perception.pose_estimator import PoseEstimator
from planning.grasp_planner import GraspPlanner
from planning.place_planner import PlacePlanner


def build_pipeline(base_dir: str):
    configs = load_all_configs(base_dir)
    frames_cfg = configs["system"].get("frames", {})

    camera_cfg = dict(configs["camera"])
    perception_cfg = dict(configs["perception"])

    # Safe default for local/sim runs: a mock camera cannot produce TNT detections.
    # If source=mock and perception mode is not mock, force mock perception.
    if str(camera_cfg.get("source", "")).lower() == "mock" and str(perception_cfg.get("mode", "")).lower() != "mock":
        perception_cfg["mode"] = "mock"

    camera = build_camera(camera_cfg)
    perception = PoseEstimator(
        camera=camera,
        perception_cfg=perception_cfg,
        markers_cfg=configs["markers"],
        transforms_cfg=configs["transforms"],
        frames_cfg=frames_cfg,
        camera_cfg=camera_cfg,
        tnt_cfg=configs.get("tnt", {}),
    )

    robot = MockRobot()
    gripper = MockGripper(configs["robot"].get("gripper", {}))
    executor = TrajectoryExecutor(robot, gripper, configs["robot"])

    grasp_planner = GraspPlanner(configs["cube"])
    place_planner = PlacePlanner(configs["grid"], configs["cube"])

    pipeline = PickPlacePipeline(
        perception=perception,
        grasp_planner=grasp_planner,
        place_planner=place_planner,
        executor=executor,
        robot=robot,
        gripper=gripper,
    )
    return pipeline, configs


def run():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    pipeline, configs = build_pipeline(base_dir)
    success_target = int(configs["system"].get("state_machine", {}).get("success_target", 1))
    successes = 0
    for _ in range(success_target):
        ok = pipeline.run_cycle()
        if not ok:
            break
        successes += 1
    return successes
