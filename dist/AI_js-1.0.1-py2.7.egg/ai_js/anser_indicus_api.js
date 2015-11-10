/*
 * Main Javascript API for AnserIndicus applications
 */

function AI_API() {
	this.is_connected = false;
}

AI_API.prototype.on_connect = function() {
	// OVERLOAD THIS!
};

AI_API.prototype.connect = function(portnum) {
	var self = this;
    /*
	var hostname = window.location.hostname;
        this.host = "";
	if (hostname == "localhost")
	{
		this.host = "ws://"+window.location.hostname+":9090/ws";	
	}
	else {
		this.host = "ws://"+window.location.hostname+":9090/ws";
	}
	*/
    if (!portnum) {
        portnum = 9090;
    }
    this.host = "ws://"+window.location.hostname+":"+portnum.toString()+"/ws";
	this.socket = new WebSocket(this.host);
	this.socket.onopen = function() {
		self.is_connected = true;
		self.on_connect.call();
	};
	this.socket.onmessage = function(msg) {
		// msg.data gives the JSON object sent
        // Called when python back-end returns
		var messageobj = JSON.parse(msg.data);    
		
		for (var fcnname in messageobj) {
			// Call function automatically based on name
            // fcnname should be something like 'data.inspect.get_database_time_range'. Split by '.'
            var fcn_name_components = fcnname.split('.');
			var fcnargs = messageobj[fcnname];
			//var on_fcnname = "on_"+fcnname;
            fcn_name_components[fcn_name_components.length - 1] = "on_"+fcn_name_components[fcn_name_components.length - 1];

            /*
            Follow the hierarchy to identify the callback function, if it exists
             */
            var o = null;
            for (var i = 0; i < fcn_name_components.length; i++) {
                if (i == 0)
                    o = self[fcn_name_components[i]];
                else
                    o = o[fcn_name_components[i]];
            }

			if (typeof o === 'function')
			{				
				o.call(self,fcnargs);   // if the callback function exists, call it!
			}
		}
	};
};

var ai_api = new AI_API();

function AI_PYTHON(api_handle) {
	this.api_handle = api_handle;
	this.json = {};
}

AI_PYTHON.prototype.call_backend = function() {
	/*
	 * stringify the JSON and send that message over the websocket to the python backend. 
	 * Eventually, backend will finish and call a callback in javascript, through the 
	 * AI_API.on_message() function, below.
	 */
	if (this.api_handle.is_connected==true) {
		this.api_handle.socket.send(JSON.stringify(this.json));
	}
};

var ai_python = new AI_PYTHON(ai_api);