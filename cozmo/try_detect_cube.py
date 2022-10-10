import cozmo
from cozmo.objects import LightCube1Id, LightCube2Id, LightCube3Id

look_around = robot.start_behavior(cozmo.behavior.BehaviorTypes.LookAroundInPlace)

cubes = robot.world.wait_until_observe_num_objects(num=3, object_type=cozmo.objects.LightCube, timeout=60)





look_around.stop()
