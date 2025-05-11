import 'dart:async';
import 'dart:io';
import 'dart:ui';

import 'package:flutter/material.dart';
import 'package:flutter_application_3/account.dart';
import 'package:flutter_application_3/map.dart';
import 'package:flutter_application_3/login.dart';

import 'package:shared_preferences/shared_preferences.dart';

import 'dart:convert';
import 'dart:developer';
import 'package:http/http.dart' as http;

import 'package:device_info_plus/device_info_plus.dart';
import 'package:flutter_background_service/flutter_background_service.dart';
import 'package:flutter_background_service_android/flutter_background_service_android.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';

//import 'package:permission_handler/permission_handler.dart';
import 'package:flutter/services.dart';

import 'package:stop_watch_timer/stop_watch_timer.dart';

//มีnotification
final FlutterLocalNotificationsPlugin flutterLocalNotificationsPlugin =
    FlutterLocalNotificationsPlugin();

Future<void> _showNotification2() async {
  AndroidNotificationDetails androidNotificationDetails =
      AndroidNotificationDetails('nextflow_noti_001', 'Urgent Alert',
          playSound: true,
          sound: RawResourceAndroidNotificationSound(
              'notification.mp3'.split('.').first),
          importance: Importance.max,
          priority: Priority.high,
          ticker: 'ticker');

  NotificationDetails platformChannelDetails = NotificationDetails(
    android: androidNotificationDetails,
  );

  await flutterLocalNotificationsPlugin.show(0, 'Emergency!',
      'Open the app to view the location.', platformChannelDetails);
}

Future<Map<String, String>> fetchData2() async {
  try {
    final response = await http.get(Uri.parse(
        'https://script.googleusercontent.com/macros/echo?user_content_key=V-WlhkWRTmYVFbQ163ThSNgPNYZr0YFzvHSKDyDK_RIeyhuugKFBsbqE_zTeiKvrX4y7iNgZjptlLYoSkIh9y2pnZ2023Jr8m5_BxDlH2jW0nuo2oDemN9CCS2h10ox_1xSncGQajx_ryfhECjZEnCmW4aT1ywfv8S2WPOhASW348Zgum1olP3Cs0bFteV2_GPqdD_kqTNb8htZ7xOkHqX5mPNaPRBKQR6uf2DyXCXrxvcxDkRzXOQ&lib=MPrA3psxMqr_nBg2_j0VAnyJ67tG3SoUN'));

    if (response.statusCode == 200) {
      // ตรวจสอบว่า response ไม่ใช่ null และเป็น JSON
      final Map<String, dynamic> jsonResponse = json.decode(response.body);

      // ตรวจสอบว่าคีย์มีอยู่ใน JSON และไม่ใช่ null
      if (jsonResponse.containsKey('reallatitude') &&
          jsonResponse.containsKey('reallongitude')) {
        String _latitude = jsonResponse['reallatitude']?.toString() ?? "0.0";
        String _longitude = jsonResponse['reallongitude']?.toString() ?? "0.0";

        print("✅ Data received: Latitude=$_latitude, Longitude=$_longitude");

        return {"latitude": _latitude, "longitude": _longitude};
      } else {
        print("⚠️ Missing keys in response JSON");
      }
    } else {
      print("❌ HTTP Error: ${response.statusCode}");
    }
  } catch (e) {
    print("❌ Error fetching ESP32 data: $e");
  }

  // คืนค่าเริ่มต้นในกรณีที่มีข้อผิดพลาด
  return {"latitude": "0.0", "longitude": "0.0"};
}

//Start Foreground&Background Service
Future<void> initializeService() async {
  //await initializeService();
  final service = FlutterBackgroundService();
  SharedPreferences prefs = await SharedPreferences.getInstance();
  await prefs.setBool(
      'hasFetchedLocation', false); //รีเซ็ตค่า Fetch ทุกครั้งที่เปิดแอป

  /// OPTIONAL, using custom notification channel id
  const AndroidNotificationChannel channel = AndroidNotificationChannel(
    'my_foreground', // id
    'MY FOREGROUND SERVICE', // title
    description:
        'This channel is used for important notifications.', // description
    importance: Importance.low, // importance must be at low or higher level
  );

  final FlutterLocalNotificationsPlugin flutterLocalNotificationsPlugin =
      FlutterLocalNotificationsPlugin();

  // if (Platform.isIOS) {
  //   await flutterLocalNotificationsPlugin.initialize(
  //     const InitializationSettings(
  //       iOS: IOSInitializationSettings(),
  //     ),
  //   );
  // }

  /*//เพิ่มขึ้นมาสำหรับ Android version14
  if (Platform.isAndroid) {
    if (await Permission.ignoreBatteryOptimizations.isDenied) {
      await Permission.ignoreBatteryOptimizations.request();
    }

    if (await Permission.notification.isDenied) {
      await Permission.notification.request();
    }

    /*if (await Permission.foregroundService.isDenied) {
      await Permission.foregroundService.request();
    }*/
  }*/

  await flutterLocalNotificationsPlugin
      .resolvePlatformSpecificImplementation<
          AndroidFlutterLocalNotificationsPlugin>()
      ?.createNotificationChannel(channel);

  await service.configure(
    androidConfiguration: AndroidConfiguration(
      // this will be executed when app is in foreground or background in separated isolate
      onStart: onStart,

      // auto start service
      autoStart: true,
      isForegroundMode: true,

      //Show Notificatiion Foreground
      notificationChannelId: 'my_foreground',
      initialNotificationTitle: 'Fall Detection Application',
      initialNotificationContent: 'The app is working.',
      foregroundServiceNotificationId: 888,
    ),
    iosConfiguration: IosConfiguration(
      // auto start service
      autoStart: true,

      // this will be executed when app is in foreground in separated isolate
      onForeground: onStart,

      // you have to enable background fetch capability on xcode project
      onBackground: onIosBackground,
    ),
  );

  service.startService();
}

@pragma('vm:entry-point')
Future<bool> onIosBackground(ServiceInstance service) async {
  WidgetsFlutterBinding.ensureInitialized();
  DartPluginRegistrant.ensureInitialized();

  SharedPreferences preferences = await SharedPreferences.getInstance();
  await preferences.reload();
  final log = preferences.getStringList('log') ?? <String>[];
  log.add(DateTime.now().toIso8601String());
  await preferences.setStringList('log', log);

  return true;
}

bool _hasFetchedLocation = false; // ป้องกันการ Fetch ซ้ำ

@pragma('vm:entry-point')
void onStart(ServiceInstance service) async {
  // Only available for flutter 3.0.0 and later
  DartPluginRegistrant.ensureInitialized();

  // โหลดค่า `_hasFetchedLocation` จาก SharedPreferences
  SharedPreferences prefs = await SharedPreferences.getInstance();
  //_hasFetchedLocation = prefs.getBool('hasFetchedLocation') ?? false;

  // For flutter prior to version 3.0.0
  // We have to register the plugin manually

  /*SharedPreferences preferences = await SharedPreferences.getInstance();
  await preferences.setString("hello", "world");*/

  /*/// OPTIONAL when use custom notification
  final FlutterLocalNotificationsPlugin flutterLocalNotificationsPlugin =
      FlutterLocalNotificationsPlugin();*/

  if (service is AndroidServiceInstance) {
    service.on('setAsForeground').listen((event) {
      service.setAsForegroundService();
    });

    service.on('setAsBackground').listen((event) {
      service.setAsBackgroundService();
    });
  }

  service.on('stopService').listen((event) {
    service.stopSelf();
  });

  // bring to foreground
  Timer.periodic(const Duration(seconds: 5), (timer) async {
    if (_hasFetchedLocation) {
      timer.cancel(); //หยุด Fetch เมื่อได้ค่าพิกัดที่ถูกต้องแล้ว
      return;
    }

    final response = await fetchData2(); // ดึงข้อมูลจาก ESP32

    String latitude = response['latitude']!;
    String longitude = response['longitude']!;
    if (latitude != "0" &&
        longitude != "0" &&
        latitude != "1" &&
        longitude != "1") {
      _showNotification2();
      _hasFetchedLocation = true; //ป้องกัน fetch ซ้ำ
      await prefs.setBool(
          'hasFetchedLocation', true); //บันทึกลงshare preference
      await prefs.setString('rememberlatitude', latitude);
      await prefs.setString('rememberlongitude', longitude);
    }

    /*// ✅ เปิด `MapsPage` อัตโนมัติ
    service.invoke(
      'open_maps',
      {
        "latitude": latitude,
        "longitude": longitude,
      },
    );*/

    // ส่งข้อมูลไปให้ UI
    service.invoke(
      'update_location',
      {
        "latitude": response['latitude'],
        "longitude": response['longitude'],
      },
    );

    if (service is AndroidServiceInstance) {
      if (await service.isForegroundService()) {
        /// OPTIONAL for use custom notification
        /// the notification id must be equals with AndroidConfiguration when you call configure() method.

        /*flutterLocalNotificationsPlugin.show(
          888,
          'COOL SERVICE',
          'Awesome ${DateTime.now()}',
          const NotificationDetails(
            android: AndroidNotificationDetails(
              'my_foreground',
              'MY FOREGROUND SERVICE',
              icon: 'ic_bg_service_small',
              ongoing: true,
            ),
          ),
        );*/

        // if you don't using custom notification, uncomment this
        // service.setForegroundNotificationInfo(
        //   title: "My App Service",
        //   content: "Updated at ${DateTime.now()}",
        // );
      }
    }

    /// you can see this log in logcat
    print('FLUTTER BACKGROUND SERVICE: ${DateTime.now()}');

    // test using external plugin
    final deviceInfo = DeviceInfoPlugin();
    String? device;
    if (Platform.isAndroid) {
      final androidInfo = await deviceInfo.androidInfo;
      device = androidInfo.model;
    }

    if (Platform.isIOS) {
      final iosInfo = await deviceInfo.iosInfo;
      device = iosInfo.model;
    }

    service.invoke(
      'update',
      {
        "current_date": DateTime.now().toIso8601String(),
        "device": device,
      },
    );
  });
}

class MyHomePage extends StatefulWidget {
  /*final String user;

  const MyHomePage({super.key, required this.user});*/
  const MyHomePage({super.key});

  //final String title;

  @override
  State<MyHomePage> createState() => _MyHomePageState();
}

//case 4 ดึงค่าจาก esp32 แล้วแสดงใน map
class _MyHomePageState extends State<MyHomePage> with WidgetsBindingObserver {
  bool _isLoading = false;
  bool _isLogout = false;
  bool _checkstatus = false;
  String _latitude = '';
  String _longitude = '';
  int countfall = 0;
  //int countfall = 0, stop = 0, i = 0;
  String _ESP32 = '';
  final _formKey = GlobalKey<FormState>();
  String? _name;
  String? _role;
  String? _username;
  //String? _latitude;
  //String? _longitude;
  //bool _serviceStarted = false;

  //Set timer
  /*final _isHours = true;*/
  Timer? _resetTimer;

  final StopWatchTimer _stopWatchTimer = StopWatchTimer(
    mode: StopWatchMode.countUp,
  );

  @override
  void initState() {
    //await initializeService(); //On Background service
    super.initState();
    _loadUser(); //โหลดข้อมูลAccount
    //_startBackgroundServiceOnce(); // เรียกแค่ครั้งแรกของหน้า
    //fetchData(); //เริ่มการfetch data แบบ auto

    WidgetsBinding.instance.addObserver(this); //สำหรับ app cycle

    /*//Start timer
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _stopWatchTimer.onStartTimer();
      _startResetTimer(1, 0); //ทุก 1 นาทีรีข้อมูลของfetchData()
      //fetchData(); //Fetch data restart
    });*/
  }

  /*Future<void> _startBackgroundServiceOnce() async {
    if (_serviceStarted) return;
    _serviceStarted = true;

    await initializeService(); // background service
  }*/

  @override
  void dispose() {
    super.dispose();
    _resetTimer?.cancel();
    _stopWatchTimer.dispose();
  }

  void _startResetTimer(int minutes, int seconds) {
    _resetTimer =
        Timer.periodic(Duration(minutes: minutes, seconds: seconds), (timer) {
      //_resetTimer = Timer.periodic(Duration(minutes: 1, seconds: 30), (timer) {
      _resetStopWatch();
    });
  }

  void _resetStopWatch() {
    setState(() {
      _stopWatchTimer.onResetTimer();
      _stopWatchTimer
          .onStartTimer(); // Restart the timer immediately after resetting
      //fetchData();

      /*
      if ((i == 0 || countfall == 0) && stop == 0) {
        //ตั้งปิดfetch auto ตอนappcycle.resumed
        fetchData(); //Fetch data restart
        stop = 1; //Set stop fetch for pause case
      }
      */
      //_showNotification2(); //Show Notification for restart
    });
  }

  //Appcycle function
  @override
  Future<void> didChangeAppLifecycleState(AppLifecycleState state) async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    _checkstatus = prefs.getBool('rememberMe') ?? false;
    //_username = prefs.getString('rememberUser'); // ดึง username ที่เคยบันทึกไว้

    super.didChangeAppLifecycleState(state);

    if (state == AppLifecycleState.paused) {
      //i = 0;
      await initializeService();
      //if (!_checkstatus && _username != null) {
      if (!_checkstatus) {
        await SetLogout2(_username!);
        /*await Future.wait([
          SetLogout2(_username!), //ให้ await ทำงานพร้อมกัน
          initializeService(),
        ]);*/
      }

      /*_stopWatchTimer.onResetTimer();
      _stopWatchTimer.onStartTimer();
      _startResetTimer(0, 5);*/
      //fetchData();
    } /*else if (state == AppLifecycleState.resumed) {
      //i = 1;
      stop = 0; //Reset stop fetch
      //_stopWatchTimer.onResetTimer();
      //_stopWatchTimer.onStartTimer();
      /*if (countfall != 0) {
        _stopWatchTimer.onResetTimer();
        _stopWatchTimer.onStartTimer();
        _startResetTimer(
            1, 0); //กรณีล้มทุก 1 นาทีรีข้อมูล อยู่หน้าแอพ ตอนนี้ยังใช้ไม่ได้
        //fetchData(); //รีข้อมูล
      } else if (countfall == 0) {
        //กรณีไม่ล้ม
        _startResetTimer(0, 5);
        //fetchData(); //รีข้อมูล
      }*/
    }*/
  }

  //ดึงข้อมูลจาก google sheet
  Future<void> fetchData() async {
    //await initializeService(); //On Background service
    setState(() {
      _isLoading = true;
      //i=0; //Reset i value
    });
    //await initializeService(); //On Background service
    try {
      final response = await http.get(
        Uri.parse(
            'https://script.googleusercontent.com/macros/echo?user_content_key=V-WlhkWRTmYVFbQ163ThSNgPNYZr0YFzvHSKDyDK_RIeyhuugKFBsbqE_zTeiKvrX4y7iNgZjptlLYoSkIh9y2pnZ2023Jr8m5_BxDlH2jW0nuo2oDemN9CCS2h10ox_1xSncGQajx_ryfhECjZEnCmW4aT1ywfv8S2WPOhASW348Zgum1olP3Cs0bFteV2_GPqdD_kqTNb8htZ7xOkHqX5mPNaPRBKQR6uf2DyXCXrxvcxDkRzXOQ&lib=MPrA3psxMqr_nBg2_j0VAnyJ67tG3SoUN'),
        //'https://script.googleusercontent.com/macros/echo?user_content_key=UzjhvIiKf-uEKJvLbf6giyIaLOEoGninpkfLSSHqgDqxzKaSP8YLeVGz5-wcfdCCkG4YR9j0B0TKsyWx5kfgvOqhW5BtzHbcm5_BxDlH2jW0nuo2oDemN9CCS2h10ox_1xSncGQajx_ryfhECjZEnC88z5TdsYJOk9wB10R2V3AQUwuXW20ilKbb2L1S3nrhyPLB7zENKN6A1thYUeE4mIkomoKDxo4kgocFVy_0Z4lntyy_SyR9ntz9Jw9Md8uu&lib=M3hzHvVTGbsuxA3AF-bU0FFyv5OXIE90q'),
      );
      log("this is the response: $response");

      if (response.statusCode == 200) {
        //แปลงข้อมูล JSON ที่ได้รับ

        final jsonResponse = json.decode(response.body);

        //final jsonResponse = json.decode(response.body) as List<dynamic>;

        // ดึงค่าจาก JSON
        final reallatitude = jsonResponse['reallatitude'];
        final reallongitude = jsonResponse['reallongitude'];
        //final latestData = jsonResponse.isNotEmpty ? jsonResponse.last : null;

        if (reallatitude != null && reallongitude != null) {
          //_showNotification(); // Show notification

          setState(() {
            _latitude = reallatitude.toString();
            _longitude = reallongitude.toString();
            //_latitude = latestData['reallatitude'].toString();
            //_longitude = latestData['reallongitude'].toString();
            _ESP32 = 'ON'; //Set ESP32 ON
            //countfall++;
            _isLoading = false;
            //_stopWatchTimer.onStopTimer;
            //_stopWatchTimer.onResetTimer;
          });

          if (_latitude != '0' &&
              _longitude != '0' &&
              _latitude != '1' &&
              _longitude != '1') {
            // Navigate to MapsPage after receiving data
            _showNotification2(); // Show notification
            countfall++;
            //_stopWatchTimer.onStopTimer;
            //_stopWatchTimer.onResetTimer;
            Navigator.push(
              context,
              MaterialPageRoute(
                builder: (context) => MapsPage(
                  latitude: _latitude,
                  longitude: _longitude,
                ),
              ),
            );
          }
        } /*else {
          // ไม่มีข้อมูลที่ต้องการ
          setState(() {
            _latitude = 'No data available';
            _longitude = 'No data available';
            _ESP32 = 'ON';
            _isLoading = false;
          });
        }*/
      } else {
        // การเชื่อมต่อล้มเหลว
        setState(() {
          _latitude = 'Failed to fetch data';
          _longitude = 'Failed to fetch data';
          _ESP32 = 'OFF';
          _isLoading = false;
        });
      }
    } catch (e) {
      log("", error: e, name: "error");
      setState(() {
        // ไม่ได้เชื่อมต่อESP32
        _latitude = 'Failed to fetch data';
        _longitude = 'Failed to fetch data';
        _ESP32 = 'OFF';
        _isLoading = false;
      });
    }
  }

  //Copy URL function
  Future<void> _copyToClipboard() async {
    // สร้าง URL โดยแทรกค่า latitude และ longitude
    final String url =
        'https://www.google.com/maps/search/?api=1&query=$_latitude,$_longitude';

    // คัดลอก URL ไปยังคลิปบอร์ด
    await Clipboard.setData(ClipboardData(text: url));

    // แสดงข้อความยืนยันการคัดลอก
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('Copied to clipboard!')),
    );
  }

  // โหลดข้อมูลUsernameจาก SharedPreferences
  Future<void> _loadUser() async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    //_username = prefs.getString('rememberUser'); // ดึง username ที่เคยบันทึกไว้
    setState(() {
      _name = prefs.getString('savedUser'); // ดึง name ที่เคยบันทึกไว้
      _username =
          prefs.getString('rememberUser'); // ดึง username ที่เคยบันทึกไว้
      _role = prefs.getString('savedrole'); // ดึง role ที่เคยบันทึกไว้
    });
  }

  //ไปหน้าAccount
  Future<void> _Account() async {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => AccountPage(
          user: _name!,
          role: _role!,
        ),
      ),
    );
  }

  Future<void> SetLogout(String username) async {
    setState(() {
      _isLogout = true; //เริ่มการโหลด
    });

    final url = Uri.parse(
      'https://script.google.com/macros/s/AKfycbwqdzf3uekN9H025xXyzCgnwYeMSkKcfulvK2l5C0NirpQVn9G5r30DlP-iKOWkjjyw/exec',
    );

    await http.post(url, body: {
      'action': 'Logout',
      'username': username,
    });

    setState(() {
      _isLogout = false; //เสร็จสิ้นการโหลด
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
    await prefs.remove('hasFetchedLocation');
    await prefs.remove('latitude');
    await prefs.remove('longitude');

    await prefs.remove('rememberstatus');
    await SetLogout(_username!);

    Navigator.pushReplacement(
      context,
      MaterialPageRoute(
        builder: (context) => const LoginPage(title: "Login"),
      ),
    );
  }

  Future<void> SetLogout2(String username) async {
    final url = Uri.parse(
      'https://script.google.com/macros/s/AKfycbwqdzf3uekN9H025xXyzCgnwYeMSkKcfulvK2l5C0NirpQVn9G5r30DlP-iKOWkjjyw/exec',
    );

    await http.post(url, body: {
      'action': 'Logout',
      'username': username,
    });
  }

  @override
  Widget build(BuildContext context) {
    return WillPopScope(
        child: Scaffold(
            appBar: AppBar(
              backgroundColor: Theme.of(context).colorScheme.inversePrimary,
              title: const Text('Fall Detection'),
              actions: [
                IconButton(
                  icon: const Icon(Icons.refresh),
                  onPressed: fetchData,
                ),
              ],
            ),
            body: SafeArea(
              child: _isLogout
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
                  : Container(
                      padding: const EdgeInsets.all(16.0),
                      child: Form(
                        key: _formKey,
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: <Widget>[
                            Center(
                              child: Align(
                                alignment: Alignment.topRight,
                                child: IconButton(
                                  icon: const Icon(Icons.account_circle),
                                  iconSize: 30,
                                  onPressed: _Account,
                                ),
                              ),
                            ),
                            if (_isLoading)
                              const CircularProgressIndicator()
                            else
                              Column(
                                children: [
                                  Text(
                                    'Latitude: $_latitude',
                                    style: const TextStyle(fontSize: 20),
                                  ),
                                  const SizedBox(height: 20),
                                  Text(
                                    'Longitude: $_longitude',
                                    style: const TextStyle(fontSize: 20),
                                  ),
                                  const SizedBox(height: 60),
                                  Center(
                                    child: Text(
                                      'ESP32: $_ESP32',
                                      style: const TextStyle(fontSize: 20),
                                    ),
                                  ),
                                ],
                              ),

                            // ใช้ Center widget เพื่อจัดให้รูปภาพอยู่ตรงกลาง
                            Center(
                              child: Column(
                                children: [
                                  Image.network(
                                    "https://files.seeedstudio.com/wiki/Wio_RP2040_mini_Dev_Board-Onboard_Wifi/Wireless-Fall-Detection-Device/fall.jpg",
                                    width: 200,
                                    height: 200,
                                  ),
                                  const Text(
                                    'Welcome to Fall Detection:',
                                  ),
                                  //เพิ่มเงื่อนไขshowปุ่ม share location เมื่อจับตำแหน่งการล้มได้
                                  if (_latitude != 'Failed to fetch data' &&
                                      _longitude != 'Failed to fetch data' &&
                                      countfall != 0)
                                    ElevatedButton(
                                      onPressed: _copyToClipboard,
                                      child: const Text('Share Location'),
                                    ),
                                  //ปุ่ม logout
                                  SizedBox(
                                    height: 15,
                                  ),
                                  Row(
                                    children: <Widget>[
                                      Expanded(
                                          child: FloatingActionButton(
                                        onPressed: (_logout),
                                        child: const Text('Logout'),
                                      ))
                                    ],
                                  ),
                                ],
                              ),
                            ),
                            //For Foreground&Background to Mapspage
                            StreamBuilder<Map<String, dynamic>?>(
                              stream:
                                  FlutterBackgroundService().on('open_maps'),
                              builder: (context, snapshot) {
                                if (snapshot.hasData) {
                                  final data = snapshot.data!;
                                  String latitude = data["latitude"] ?? "0";
                                  String longitude = data["longitude"] ?? "0";

                                  // ✅ นำทางไปหน้า MapsPage อัตโนมัติเมื่อได้รับค่าพิกัด
                                  WidgetsBinding.instance
                                      .addPostFrameCallback((_) {
                                    Navigator.push(
                                      context,
                                      MaterialPageRoute(
                                        builder: (context) => MapsPage(
                                          latitude: latitude,
                                          longitude: longitude,
                                        ),
                                      ),
                                    );
                                  });
                                }
                                return SizedBox
                                    .shrink(); // ไม่แสดง UI อะไรเลยถ้ายังไม่มีข้อมูล
                              },
                            ),
                          ],
                        ),
                      ),
                    ),
            )),
        onWillPop: () async {
          return false;
        });
  }
}
