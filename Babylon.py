class Babylon():
	def __init__(self):
		self.chirp = ""
		self.pump = ""
	def confirm_identity(self):
		for device in ["ACM0","ACM1"]:
			print "testing device: ",device
			dev = serial.Serial("/dev/tty%s" % (device,),9600)
			serial_input = dev.readline().strip()

			if serial_input == 

                identity_confirmed = False
                
                        try:
                                for device in ["ACM0","ACM1"]:
                                        print "Testing device ",device
                                        dev = serial.Serial('/dev/tty%s' % (device,), 9600)
                                        serial_input =  dev.readline().strip()
                                        print "Got input: ",serial_input
                                        if serial_input == "c": self.chirp
                                                print "Device ",device," is the chirp. Attempting to complete transaction"
                                                end_transaction = ""
                                                while end_transaction != "ok":
                                                        dev.write("confirmed")
                                                        identity_confirmed = True
                                                        end_transaction = self.chirp.readline().strip()
                                                        if end_transaction == "ok":
                                                                print "Transaction complete. Chirp identity: ",device
                                                                return

                        except Exception as e:
                                print self.confirm_identity.__name__," ",e
