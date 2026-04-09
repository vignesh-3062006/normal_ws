#include <micro_ros_arduino.h>
#include <AccelStepper.h>
#include <ESP32Servo.h>
#include <rcl/rcl.h>
#include <rclc/rclc.h>
#include <rclc/executor.h>
#include <std_msgs/msg/float32_multi_array.h>
#include <sensor_msgs/msg/joint_state.h>

#define STEP_PIN 14
#define DIR_PIN  13
#define SERVO_PIN 26

AccelStepper stepper(AccelStepper::DRIVER, STEP_PIN, DIR_PIN);
Servo servo;
rcl_clock_t ros_clock;

float stepsPerMM = 6.25;
long targetPosition = 0;
int servoPos = 0;
const int servoMin = 0;
const int servoMax = 68;

bool motorEnabled = false;
unsigned long stopTime = 0;
unsigned long lastPublishTime = 0;
const unsigned long PUBLISH_INTERVAL_MS = 50; // 20Hz publish rate

volatile bool newCommand = false;
volatile float pendingDistance = 0.0;
volatile int   pendingServo   = -1;
bool motion_in_progress = false;

// Subscriber
rcl_subscription_t subscriber;
std_msgs__msg__Float32MultiArray msg;
float msg_data[2];

// Publisher
rcl_publisher_t joint_state_publisher;
sensor_msgs__msg__JointState joint_state_msg;

// Joint state message buffers
#define NUM_JOINTS 2
double joint_positions[NUM_JOINTS];
double joint_velocities[NUM_JOINTS];
double joint_efforts[NUM_JOINTS];

// Joint name strings
char joint1_name[] = "linear_joint";  // match your URDF joint name
char joint2_name[] = "servo_joint";    // match your URDF joint name
char * joint_names[NUM_JOINTS] = { joint1_name, joint2_name };

rosidl_runtime_c__String joint_name_array[NUM_JOINTS];

rclc_executor_t executor;
rclc_support_t  support;
rcl_allocator_t allocator;
rcl_node_t      node;


void arm_callback(const void * msgin)
{
  const std_msgs__msg__Float32MultiArray * m =
    (const std_msgs__msg__Float32MultiArray *)msgin;

  if (m->data.size >= 1 && !motion_in_progress)
  {
    pendingDistance = m->data.data[0];
    newCommand = true;
    motion_in_progress = true;
  }
}

void setup()
{
  Serial.begin(115200);

  stepper.setMaxSpeed(1500);
  stepper.setAcceleration(1000);
  servo.attach(SERVO_PIN);
  servo.write(servoPos);

  set_microros_transports();
  delay(2000);

  allocator = rcl_get_default_allocator();
  rclc_support_init(&support, 0, NULL, &allocator);
  rclc_node_init_default(&node, "arm_controller_node", "", &support);

  // --- Subscriber setup ---
  msg.data.data     = msg_data;
  msg.data.size     = 0;
  msg.data.capacity = 2;

  rclc_subscription_init_default(
    &subscriber,
    &node,
    ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Float32MultiArray),
    "arm_command");

  // --- Joint state publisher setup ---
  rclc_publisher_init_default(
    &joint_state_publisher,
    &node,
    ROSIDL_GET_MSG_TYPE_SUPPORT(sensor_msgs, msg, JointState),
    "joint_states");  // this topic name is what RViz/robot_state_publisher listens to
  rcl_clock_init(RCL_SYSTEM_TIME, &ros_clock, &allocator);

  // Attach buffers to joint state message
  joint_state_msg.name.data     = joint_name_array;
  joint_state_msg.name.size     = NUM_JOINTS;
  joint_state_msg.name.capacity = NUM_JOINTS;

  for (int i = 0; i < NUM_JOINTS; i++) {
    joint_state_msg.name.data[i].data     = joint_names[i];
    joint_state_msg.name.data[i].size     = strlen(joint_names[i]);
    joint_state_msg.name.data[i].capacity = strlen(joint_names[i]) + 1;
  }

  joint_state_msg.position.data     = joint_positions;
  joint_state_msg.position.size     = NUM_JOINTS;
  joint_state_msg.position.capacity = NUM_JOINTS;

  joint_state_msg.velocity.data     = joint_velocities;
  joint_state_msg.velocity.size     = NUM_JOINTS;
  joint_state_msg.velocity.capacity = NUM_JOINTS;

  joint_state_msg.effort.data     = joint_efforts;
  joint_state_msg.effort.size     = NUM_JOINTS;
  joint_state_msg.effort.capacity = NUM_JOINTS;

  // Executor handles subscriber only (publisher is manual)
  rclc_executor_init(&executor, &support.context, 1, &allocator);
  rclc_executor_add_subscription(
    &executor, &subscriber, &msg, &arm_callback, ON_NEW_DATA);
}

void publishJointStates()
{
  double stepperPosMM = (double)stepper.currentPosition() / stepsPerMM;
  joint_positions[0] = stepperPosMM / 1000.0;
  joint_positions[1] = (double)servoPos * (3.14159265 / 180.0);

  joint_velocities[0] = (double)stepper.speed() / (stepsPerMM * 1000.0);
  joint_velocities[1] = 0.0;

  joint_efforts[0] = 0.0;
  joint_efforts[1] = 0.0;

  // Use millis() for timestamp — no rcl_clock needed
  rcl_time_point_value_t now;
  rcl_clock_get_now(&ros_clock, &now);

  joint_state_msg.header.stamp.sec =
      (int32_t)(now / 1000000000ULL);

  joint_state_msg.header.stamp.nanosec =
      (uint32_t)(now % 1000000000ULL);

    rcl_publish(&joint_state_publisher, &joint_state_msg, NULL);
  }

void loop()
{
  rclc_executor_spin_some(&executor, RCL_MS_TO_NS(1));

    if (newCommand) {
    newCommand = false;
    long steps = (long)(pendingDistance * stepsPerMM);  // e.g. 1136mm * 50 = 56800
    targetPosition = steps;   // ← ABSOLUTE, not +=
    stepper.enableOutputs();
    motorEnabled = true;
    stepper.moveTo(targetPosition);
    }

    if (pendingServo >= servoMin && pendingServo <= servoMax) {
      servoPos = pendingServo;
      servo.write(servoPos);
    }

  stepper.run();

  if (stepper.distanceToGo() == 0 && motorEnabled) {
    if (stopTime == 0) stopTime = millis();
    if (millis() - stopTime > 1000) {
      motorEnabled = false;
      motion_in_progress = false;
    }
  } else {
    stopTime = 0;
  }

  // Publish joint states at 20Hz
  unsigned long now = millis();
  if (now - lastPublishTime >= PUBLISH_INTERVAL_MS) {
    lastPublishTime = now;
    publishJointStates();
  }
}