import aind_behavior_experiment_launcher.launcher.behavior_launcher as behavior_launcher
from aind_behavior_experiment_launcher.apps.app_service import BonsaiApp
from aind_behavior_experiment_launcher.resource_monitor.resource_monitor_service import (
    ResourceMonitor,
    available_storage_constraint_factory,
    remote_dir_exists_constraint_factory,
)
from aind_behavior_services.session import AindBehaviorSessionModel

from aind_behavior_force_foraging.rig import AindForceForagingRig
from aind_behavior_force_foraging.task_logic import AindForceForagingTaskLogic


def make_launcher():
    data_dir = r"C:/Data"
    remote_dir = r"\\allen\aind\scratch\vr-foraging"
    srv = behavior_launcher.BehaviorServicesFactoryManager()
    srv.bonsai_app = BonsaiApp(r"./src/main.bonsai")
    srv.data_transfer = behavior_launcher.robocopy_data_transfer_factory(remote_dir)
    srv.resource_monitor = ResourceMonitor(
        constrains=[
            available_storage_constraint_factory(data_dir, 2e11),
            remote_dir_exists_constraint_factory(remote_dir),
        ]
    )

    return behavior_launcher.BehaviorLauncher(
        rig_schema_model=AindForceForagingRig,
        session_schema_model=AindBehaviorSessionModel,
        task_logic_schema_model=AindForceForagingTaskLogic,
        data_dir=data_dir,
        config_library_dir=r"\\allen\aind\scratch\AindBehavior.db\AindForceForaging",
        temp_dir=r"./local/.temp",
        repository_dir=None,
        allow_dirty=False,
        skip_hardware_validation=False,
        debug_mode=False,
        group_by_subject_log=True,
        services=srv,
        validate_init=True,
    )


if __name__ == "__main__":
    launcher = make_launcher()
    launcher.main()