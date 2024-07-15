import requests
import time
import pandas as pd
import datetime
from pythonosc import udp_client

def get_data_from_api(url, username, password):
	try:
		response = requests.get(url, auth=(username, password))
		devices = response.json()
		ActivePower = devices[0]['ActivePower'] * 1000
		Voltage = devices[0]['Voltage']
		Current = devices[0]['Current']
		PowerFactor = devices[0]['PowerFactor']
		Temperature = devices[0]['Temperature']
		return Voltage, Current, ActivePower, PowerFactor, Temperature

	except Exception as e:
		print(f"Error fetching data: {e}")
		return None, None, None, None, None

def is_css(power):
    CSS_THRESHOLD = 2e-5  # found by experiments
    return power < CSS_THRESHOLD

def main():

	# Smart-me API
	url = "https://api.smart-me.com/api/Devices/"
	username = "" # your username at smart-me
	password = "" # your password at smart-me
	# Name of the file to save the data
	save_file_name = "measured_energy_css.csv"

	Voltage_list, Current_list, ActivePower_list, Energy_list = [], [], [], []
	Time_list, State_list = [], []
	state = 'css'
	old_time = time.time()
	print('Start measuring the energy consumption...')

	while True:

		print("-" * 30)

		Voltage, Current, ActivePower, _, _ = get_data_from_api(url, username, password)
		if ActivePower is None:
			continue

		current_time = time.time()
		time_show = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		print(f"receiving new data from smart-me at {time_show}")

		time_interval = current_time - old_time
		old_time = current_time
		energy = (ActivePower / 1000) * (time_interval / 3600) # energy in kWh
		print(f"Energy consumed in this interval is {energy}")

		if state == "css" and not is_css(energy):
			print("GPU starts working. Measuring the real-time consumption...")
			state = "training"
		elif state == "training" and is_css(energy):
			print("GPU back to css. End of the measuring.")
			break
		elif state == "training" and not is_css(energy):
			print("GPU continues working.")
		else:
			print("GPU is in css state.")

		Voltage_list.append(Voltage)
		Current_list.append(Current)
		ActivePower_list.append(ActivePower)
		Energy_list.append(energy)
		Time_list.append(time_show)
		State_list.append(state)

		time.sleep(1)

		# client.send_message("/smart-me/Voltage", Voltage)
		# client.send_message("/smart-me/Current", Current)
		# client.send_message("/smart-me/Power", ActivePower)
		# client.send_message("/smart-me/Energy", energy) # energy in kWh

	df = pd.DataFrame({
		'Time': Time_list,
		'State': State_list,
		'Voltage': Voltage_list,
		'Current': Current_list,
		'ActivePower': ActivePower_list,
		'Energy': Energy_list
	})
	df.to_csv(save_file_name, index=False)
	print("Final data saved to CSV file.")

if __name__ == "__main__":

	# OSC protocol
	# ip_local_osc = "" # your IP address of the local device(laptop)
	# port_osc = 5011 # osc port where the data will be sent
	# client = udp_client.SimpleUDPClient(ip_local_osc, port_osc)
	# print('Sending data through OSC protocol')
	# print('-'*30)
	main()