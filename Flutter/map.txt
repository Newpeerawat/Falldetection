import 'package:flutter/material.dart';
//import 'dart:convert';
import 'package:longdo_maps_api3_flutter/longdo_maps_api3_flutter.dart';
import 'package:geolocator/geolocator.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter_application_3/login.dart';
import 'package:flutter_application_3/home.dart';
import 'package:http/http.dart' as http;
//import 'package:flutter_application_3/home.dart';
import 'package:flutter/services.dart';

//import 'dart:async';

/*//case3 พิมพ์latitudeและlongitudeแล้วแสดงในmap
class MapsPage extends StatefulWidget {
  final String? latitude;
  final String? longitude;

  const MapsPage({Key? key, this.latitude, this.longitude}) : super(key: key);

  @override
  State<MapsPage> createState() => _MapsPageState();
}

class _MapsPageState extends State<MapsPage> {
  final map = GlobalKey<LongdoMapState>();
  final GlobalKey<ScaffoldMessengerState> messenger =
      GlobalKey<ScaffoldMessengerState>();

  String? latitude;
  String? longitude;

  @override
  Widget build(BuildContext context) {
  return Scaffold(
    appBar: AppBar(
      title: const Text('Map'),
    ),
    body: Column(
      children: [
        Expanded(
          flex: 2,
          child: LongdoMapWidget(
            apiKey: "330c3103963b7f4bd6aea126b985c041",
            key: map,
            eventName: [
              JavascriptChannel(
                      name: "ready",
                      onMessageReceived: (message) {
                        // Check if latitude and longitude are available, then add marker
                      if (widget.latitude != null && widget.longitude != null) {
                        print("Location"); //เช็ค
                        addMarker(double.parse(widget.latitude!), double.parse(widget.longitude!));
                      }
                      },
                    ),
              /*JavascriptChannel(
                  name: "click",
                  onMessageReceived: (message) {
                    var jsonObj = json.decode(message.message);
                    setState(() {
                      latitude = jsonObj['data']['lat'].toString();
                      longitude = jsonObj['data']['lon'].toString();
                    });
                    print(
                        'Latitude: $latitude, Longitude: $longitude'); //บอกตำแหน่งที่กด
                    addMarker(
                        double.parse(latitude!), double.parse(longitude!));
                  },
                ),*/
                /*JavascriptChannel(
                  name: "overlayClick",
                  onMessageReceived: (message) {
                    var jsonObj = json.decode(message.message);
                    map.currentState
                        ?.call("Overlays.remove", args: [jsonObj["data"]]);
                  },
                ),*/
            ],
          ),
        ),
        
        // Show latitude and longitude
        if (widget.latitude != null && widget.longitude != null)
          Text('Latitude: ${widget.latitude}, Longitude: ${widget.longitude}'),
        ElevatedButton(
          onPressed: () {
            Navigator.pop(context, {'latitude': widget.latitude, 'longitude': widget.longitude});
          },
          child: const Text('Back to Home'),
        ),
      ],
    ),
  );
}
  //function addMarker
  void addMarker(double lat, double lon) {
    var marker = Longdo.LongdoObject(
      "Marker",
      args: [
        {
          "lon": lon,
          "lat": lat,
        },
        {"draggable": true}
      ],
    );
    map.currentState?.call("Overlays.add", args: [marker]);
    print('Marker added at Latitude: $lat, Longitude: $lon'); // ใส่ print ที่นี่เพื่อตรวจสอบการทำงานของ addMarker()
  }
}*/

//พิมพ์latitudeและlongitudeแล้วแสดงในmapพร้อมตำแหน่งล่าสุด(ฉบับล่าสุด)
class MapsPage extends StatefulWidget {
  final String? latitude;
  final String? longitude;

  const MapsPage({Key? key, this.latitude, this.longitude}) : super(key: key);

  @override
  State<MapsPage> createState() => _MapsPageState();
}

class _MapsPageState extends State<MapsPage> {
  final map = GlobalKey<LongdoMapState>();
  final GlobalKey<ScaffoldMessengerState> messenger =
      GlobalKey<ScaffoldMessengerState>();
  bool _isLoading = false;
  String? _username;

  String? latitude;
  String? longitude;

  //function Marker(ตอนนี้ไม่ได้ใช้)
  void addMarker(
    double lat,
    double lon,
  ) {
    var marker = Longdo.LongdoObject(
      "Marker",
      args: [
        {
          "lon": lon,
          "lat": lat,
        },

        {
          "title": "Destination",
          "detail": "Patient",
        }
        //{"draggable": true} //ตั้งเพื่อลากหมุดได้
      ],
    );
    map.currentState?.call("Overlays.add", args: [marker]);
    //map.currentState?.call("Overlays.drop", args: [marker]); //Drop pin
    map.currentState
        ?.call("Overlays.bounce", args: [marker]); // Show bounce animation
    print(
        'Marker added at Latitude: $lat, Longitude: $lon'); // ใส่ print ที่นี่เพื่อตรวจสอบการทำงานของ addMarker()
  }

  void currentMarker(double lat, double lon) {
    var marker2 = Longdo.LongdoObject(
      "Dot",
      args: [
        {
          "lon": lon,
          "lat": lat,
        },
        {
          "title": "Start",
          "detail": "Me",
          "lineWidth": 10, //ความหนาจุด
          "lineColor": "rgba(0, 0, 255, 0.8)", //Red Green Blue โปร่งแสง
          //"draggable": true,

          /*//โชว์คำพูด marker บนmap
          "icon":{
            "html": "<b>Marker</b>", 
            /*"offset": {
                        "x": 18,
                        "y": 21,
                      }*/
          },*/
        }
        //{ 'title': 'Marker', 'detail': 'Marker', 'icon': { 'url': 'assets/image/Map_Marker.png', 'offset': { 'x': 16, 'y': 16 }} }
      ],
    );
    map.currentState?.call("Overlays.add", args: [marker2]);
    print(
        'Marker added at Latitude: $lat, Longitude: $lon'); // ใส่ print ที่นี่เพื่อตรวจสอบการทำงานของ currentMarker()
  }

  //function navigation
  void navigation(
      double latstart, double lonstart, double latend, double lonend) {
    // สร้าง marker สำหรับจุดเริ่มต้น (start)
    var start = {
      "lon": lonstart,
      "lat": latstart,
    };

    // สร้าง marker สำหรับจุดปลายทาง (end)
    var end = Longdo.LongdoObject(
      "Marker",
      args: [
        {
          "lon": lonend,
          "lat": latend,
        },
        {
          "title": "Destination",
          "detail": "Patient",
        },
      ],
    );

    // เพิ่ม marker สำหรับ end ลงในแผนที่
    map.currentState?.call("Overlays.add", args: [end]);
    // ทำให้ marker ของ end แสดง animation (bounce)
    map.currentState?.call("Overlays.bounce", args: [end]);

    /*
    // สร้าง Polyline สำหรับแสดงเส้นทาง
    var polyline = Longdo.LongdoObject(
      "Polyline",
      args: [
        [
          {"lon": lonstart, "lat": latstart},
          {"lon": lonend, "lat": latend},
        ],
        {
          "color": "blue", // สีของเส้น
          "lineWidth": 5, // ความหนาของเส้น
        }
      ],
    );

    // เพิ่ม Polyline ลงในแผนที่
    map.currentState?.call("Overlays.add", args: [polyline]);
    */

    // ตั้งเส้นทางจาก start ไปยัง end
    map.currentState
        ?.call("Route.clear", args: []); // เคลียร์เส้นทางเก่าทั้งหมด
    map.currentState
        ?.call("Route.add", args: [start]); // เพิ่มจุดเริ่มต้น (start)
    map.currentState?.call("Route.add", args: [end]); // เพิ่มจุดปลายทาง (end)

    // คำนวณและแสดงเส้นทางจาก start ไปยัง end
    map.currentState?.call("Route.search", args: []);
  }

  //Function get location
  getLocation() async {
    //Current location
    LocationPermission permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied ||
        permission == LocationPermission.deniedForever) {
      print("Location Denied");
      LocationPermission ask = await Geolocator.requestPermission();
    } else {
      Position currentposition = await Geolocator.getCurrentPosition(
          desiredAccuracy: LocationAccuracy.best);
      print("Latitude=${currentposition.latitude.toString()}");
      print("Longitude=${currentposition.longitude.toString()}");

      //currentMarker(double.parse(currentposition.latitude.toString()),double.parse(currentposition.longitude.toString()));

      //Call Navigation
      navigation(
          double.parse(currentposition.latitude.toString()),
          double.parse(currentposition.longitude.toString()),
          double.parse(widget.latitude!),
          double.parse(widget.longitude!));

      /*map.currentState?.call("Ui.Geolocation.visible",
          args: [true]); //Show Current location symbol*/

      //ให้ตอนstartหน้าmapไปอยู่ที่Patient Location
      var location = {
        "lon": double.parse(widget.longitude!),
        "lat": double.parse(widget.latitude!),
      };
      map.currentState?.call("location", args: [location]);
      //map.currentState?.call("location", args: ["LatLng(${currentposition.latitude.toString()}, ${currentposition.longitude.toString()})"]);
    }
  }

  Future<void> SetLogout(String username) async {
    setState(() {
      _isLoading = true; //เริ่มการโหลด
    });

    final url = Uri.parse(
      'https://script.google.com/macros/s/AKfycbwqdzf3uekN9H025xXyzCgnwYeMSkKcfulvK2l5C0NirpQVn9G5r30DlP-iKOWkjjyw/exec',
    );

    await http.post(url, body: {
      'action': 'Logout',
      'username': username,
    });

    setState(() {
      _isLoading = false; //เสร็จสิ้นการโหลด
    });

    /*if (response.statusCode == 200) {
      final result = jsonDecode(response.body);
      print("✅ ${result['message']}");
    } else {
      print("❌ Failed to delete user");
    }*/
  }

  //Logout
  Future<void> _logout() async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    setState(() {
      _username =
          prefs.getString('rememberUser'); // ดึง username ที่เคยบันทึกไว้
    });

    await prefs.remove('rememberstatus');
    await SetLogout(_username!);

    await prefs.remove('hasFetchedLocation');
    await prefs.remove('latitude');
    await prefs.remove('longitude');

    Navigator.pushReplacement(
      context,
      MaterialPageRoute(
        builder: (context) => const LoginPage(title: "Login"),
      ),
    );
  }

  //Copy URL function
  Future<void> _copyToClipboard() async {
    // สร้าง URL โดยแทรกค่า latitude และ longitude
    final String url =
        'https://www.google.com/maps/search/?api=1&query=${widget.latitude},${widget.longitude}';

    // คัดลอก URL ไปยังคลิปบอร์ด
    await Clipboard.setData(ClipboardData(text: url));

    // แสดงข้อความยืนยันการคัดลอก
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('Copied to clipboard!')),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
        appBar: AppBar(
          title: const Text('Map'),
        ),
        body: SafeArea(
          child: _isLoading
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      CircularProgressIndicator(),
                      SizedBox(height: 12),
                      Text("Logout....."),
                    ],
                  ),
                )
              : Column(
                  children: [
                    Expanded(
                      flex: 2,
                      child: LongdoMapWidget(
                        apiKey: "330c3103963b7f4bd6aea126b985c041",
                        key: map,
                        eventName: [
                          JavascriptChannel(
                            name: "ready",
                            onMessageReceived: (message) {
                              /*// Check if latitude and longitude are available, then add marker for destination
                    if (widget.latitude != null && widget.longitude != null) {
                      addMarker(double.parse(widget.latitude!),
                          double.parse(widget.longitude!));
                    }*/

                              //get location
                              getLocation();
                            },
                          ),
                        ],
                      ),
                    ),

                    // Show latitude and longitude on app
                    if (widget.latitude != null && widget.longitude != null)
                      Text(
                          'Latitude: ${widget.latitude}, Longitude: ${widget.longitude}'),
                    // Button to get current location
                    /*ElevatedButton(
            //onPressed: getCurrentLocation,
            onPressed: test,
            child: const Text('Get Current Location'),
          ),*/

                    //ให้อยู่บรรทัดเดียวกันในแนวนอน
                    Row(
                      mainAxisAlignment: MainAxisAlignment
                          .spaceEvenly, // จัดวางปุ่มให้มีระยะห่างเท่ากัน
                      children: [
                        //ปุ่ม My Location
                        ElevatedButton(
                          onPressed: () async {
                            Position currentposition =
                                await Geolocator.getCurrentPosition(
                                    desiredAccuracy: LocationAccuracy.best);
                            var location = {
                              "lon": double.parse(
                                  currentposition.longitude.toString()),
                              "lat": double.parse(
                                  currentposition.latitude.toString()),
                            };
                            map.currentState
                                ?.call("location", args: [location]);
                          },
                          child: const Text('My Location'),
                        ),
                        //ปุ่ม Patient Location
                        ElevatedButton(
                          onPressed: () {
                            var location = {
                              "lon": double.parse(widget.longitude!),
                              "lat": double.parse(widget.latitude!),
                            };
                            map.currentState
                                ?.call("location", args: [location]);
                          },
                          child: const Text('Patient Location'),
                        ),
                      ],
                    ),

                    //ให้อยู่บรรทัดเดียวกันในแนวนอน
                    Row(
                      mainAxisAlignment: MainAxisAlignment
                          .spaceEvenly, // จัดวางปุ่มให้มีระยะห่างเท่ากัน
                      children: [
                        ElevatedButton(
                          onPressed: (_copyToClipboard),
                          child: const Text('Share Location'),
                        ),
                        ElevatedButton(
                          onPressed: () {
                            /*Navigator.pop(context, {
                              'latitude': widget.latitude,
                              'longitude': widget.longitude
                            });*/
                            Navigator.pushReplacement(
                              context,
                              MaterialPageRoute(
                                builder: (context) => const MyHomePage(),
                              ),
                            ); //ไปหน้าHomePage
                          },
                          child: const Text('Back to Home'),
                        ),
                      ],
                    ),

                    ElevatedButton(
                      onPressed: (_logout),
                      child: const Text('Logout'),
                    ),
                  ],
                ),
        ));
  }
}
