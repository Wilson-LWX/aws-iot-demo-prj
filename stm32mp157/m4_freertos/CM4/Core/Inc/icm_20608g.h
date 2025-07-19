/*
 * icm_20608g.h
 *
 *  Created on: Jun 7, 2025
 *      Author: wxliu
 */

#include <stdint.h>
#include <string.h>

#ifndef INC_ICM_20608G_H_
#define INC_ICM_20608G_H_

// Select either POLL or INTERRUPT
#define GYRO_MODE_POLL
//#define GYRO_MODE_INT

/****************** Write and Read Cmd ******************/
#define ICM_WRITE							(0x00)
#define ICM_READ							(0x80)

/****************** Device ID ******************/
#define ICM20608G_ID						(0xAF)
#define ICM20608D_ID						(0xAE)

/****************** Register Map ******************/
#define ICM_SELF_TEST_X_GYRO				(0x00)
#define ICM_SELF_TEST_Y_GYRO				(0x01)
#define ICM_SELF_TEST_Z_GYRO				(0x02)

#define ICM_SELF_TEST_X_ACCEL				(0x0D)
#define ICM_SELF_TEST_Y_ACCEL				(0x0E)
#define ICM_SELF_TEST_Z_ACCEL				(0x0F)

#define ICM_XG_OFFS_USRH					(0x13)
#define ICM_XG_OFFS_USRL					(0x14)
#define ICM_YG_OFFS_USRH					(0x15)
#define ICM_YG_OFFS_USRL					(0x16)
#define ICM_ZG_OFFS_USRH					(0x17)
#define ICM_ZG_OFFS_USRL					(0x18)

#define ICM_SMPLRT_DIV						(0x19)

#define ICM_CONFIG							(0x1A)	// Bits[7]:RSV; Bits[6]:FIFO-MODE; Bits[5:3]:EXT_SYNC_SET; Bits[2:0]:DLPF_CFG
#define ICM_GYRO_CONFIG						(0x1B)	// Bits[7:6:5]:XG:YG:ZG_ST; Bits[4:3]:FS_SEL; Bits[2]:RSV; Bits[1:0]:FCHOICE_B
#define ICM_ACCEL_CONFIG					(0x1C)	// Bits[7:6:5]:XA:YA:ZA_ST; Bits[4:3]:ACCEL_FS_SEL; Bits[2:0]:RSV
#define ICM_ACCEL_CONFIG_2					(0x1D)	// Bits[7:6]:RSV; Bits[5:4]:DEC2_CFG; Bits[3]:ACCEL_FCHOI_CE_B;	Bits[2:0]:A_DLPF_CFG
#define ICM_LP_MODE_CFG						(0x1E)	//

#define ICM_ACCEL_WOM_THR					(0x1F)

#define ICM_FIFO_EN							(0x23)

#define ICM_FSYNC_INT						(0x36)
#define ICM_INT_PIN_CFG						(0x37)
#define ICM_INT_ENABLE						(0x38)
#define ICM_INT_STATUS						(0x3A)

#define ICM_ACCEL_XOUT_H					(0x3B)
#define ICM_ACCEL_XOUT_L					(0x3C)
#define ICM_ACCEL_YOUT_H					(0x3D)
#define ICM_ACCEL_YOUT_L					(0x3E)
#define ICM_ACCEL_ZOUT_H					(0x3F)
#define ICM_ACCEL_ZOUT_L					(0x40)

#define ICM_TEMP_OUT_H						(0x41)
#define ICM_TEMP_OUT_L						(0x42)

#define ICM_GYRO_XOUT_H						(0x43)
#define ICM_GYRO_XOUT_L						(0x44)
#define ICM_GYRO_YOUT_H						(0x45)
#define ICM_GYRO_YOUT_L						(0x46)
#define ICM_GYRO_ZOUT_H						(0x47)
#define ICM_GYRO_ZOUT_L						(0x48)

#define ICM_SIGNAL_PATH_RESET				(0x68)
#define ICM_ACCEL_INTEL_CTRL				(0x69)
#define ICM_USER_CTRL						(0x6A)
#define ICM_PWM_MGMT_1						(0x6B)
#define ICM_PWM_MGMT_2						(0x6C)

#define ICM_FIFO_COUNTH						(0x72)
#define ICM_FIFO_COUNTL						(0x73)
#define ICM_FIFO_R_W						(0x74)
#define ICM_WHO_AM_I						(0x75)
#define ICM_XA_OFFSET_H						(0x77)
#define ICM_XA_OFFSET_L						(0x78)
#define ICM_YA_OFFSET_H						(0x7A)
#define ICM_YA_OFFSET_L						(0x7B)
#define ICM_ZA_OFFSET_H						(0x7D)
#define ICM_ZA_OFFSET_L						(0x7E)

#define GYRO_EXC_BYTE_LEN 8  //14-with acc 8-no acc
#define GYRO_EXC_BYTE_LEN_PLUS_ONE 9 //15
#define FRAME_HEAD 0x5E7FF7E5

typedef struct
{
    uint32_t frameHead;      // frame edge alignment，fixed as 0x5E7FF7E5
    uint32_t frameNo;        // frame number count
    float temperature;
    //float gyro_x_acc;      // no ACC reporting
    //float gyro_y_acc;
    //float gyro_z_acc;
    float gyro_x_vel;
    float gyro_y_vel;
    float gyro_z_vel;
    uint32_t checkSum;       // checkSum to valid in the peer
} ICM_Data_t;

typedef struct
{
	uint8_t rawBuf[GYRO_EXC_BYTE_LEN_PLUS_ONE];
} ICM_Raw_Data_t;

typedef enum
{
	ICM_GYRO_STATE_NULL = 0,
	ICM_GYRO_STATE_ON = 1,
	ICM_GYRO_STATE_OFF = 2,
	// ICM_GYRO_STATE_RESETTING = 3,
}ICM_Gyro_State;

/********************************************/
void ICM_Init(void);
void ICM_Disable(void);
void ICM_ReadGyroAccel(ICM_Data_t *data);
void ICM_GyroCalibrateOffset(uint16_t sample_count);
/********************************************/

#endif /* INC_ICM_20608G_H_ */
