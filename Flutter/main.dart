import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_application_3/login.dart';

import 'package:flutter_local_notifications/flutter_local_notifications.dart';

//มีnotification //พร้อมapp cycle
final FlutterLocalNotificationsPlugin flutterLocalNotificationsPlugin =
    FlutterLocalNotificationsPlugin();

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  const AndroidInitializationSettings initializationSettingsAndroid =
      AndroidInitializationSettings("@mipmap/ic_launcher");

  final InitializationSettings initializationSettings =
      InitializationSettings(android: initializationSettingsAndroid);

  await flutterLocalNotificationsPlugin.initialize(initializationSettings);

  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  // This widget is the root of your application.
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Fall Detection',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.lightBlue),
        useMaterial3: true,
      ),
      home: const LoginPage(title: 'Login'),
    );
  }
}

/*class MyHomePage extends StatefulWidget {
  const MyHomePage({super.key, required this.title});

  final String title;

  @override
  State<MyHomePage> createState() => _MyHomePageState();
}

//case 4 ดึงค่าจาก esp32 แล้วแสดงใน map
class _MyHomePageState extends State<MyHomePage> with WidgetsBindingObserver {
  bool _isLoading = false;
  String _latitude = '';
  String _longitude = '';
  int countfall = 0, i=0;
  String _ESP32 = '';
  final _formKey = GlobalKey<FormState>();
  //String? _latitude;
  //String? _longitude;

  //Set timer
  /*final _isHours = true;*/
  Timer? _resetTimer;

  final StopWatchTimer _stopWatchTimer = StopWatchTimer(
    mode: StopWatchMode.countUp,
  );

  @override
  void initState() {
    super.initState();
    fetchData(); //เริ่มการfetch data แบบ auto

    WidgetsBinding.instance.addObserver(this); //สำหรับ app cycle

    //Start timer
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _stopWatchTimer.onStartTimer();
      _startResetTimer(2,0); //ทุก 2 นาทีรีข้อมูล
      //fetchData(); //Fetch data restart
    });
  }

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
      if(i==0 || countfall==0){ //ตั้งปิดfetch auto ตอนappcycle.resumed
        fetchData(); //Fetch data restart
      }
      //_showNotification(); //Show Notification for restart
    });
  }

  //Appcycle function
  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    super.didChangeAppLifecycleState(state);
    /*if (state == AppLifecycleState.paused ||
        state == AppLifecycleState.inactive) {
      if (countfall != 0) { //มีการล้มแล้ว
        _stopWatchTimer.onResetTimer();
        _stopWatchTimer.onStartTimer();
        _startResetTimer(2, 0);
      } 
      else { //ยังไม่ล้ม
        //fetchData(); //รีข้อมูล
        _stopWatchTimer.onResetTimer();
        _stopWatchTimer.onStartTimer();
        _startResetTimer(0,20); //ทุก 20 วินาทีรีข้อมูล; //ให้สามารถทำงานได้ขณะไม่เปิดแอพพร้อมresetเวลาใหม่
        //fetchData(); //ให้สามารถทำงานได้ขณะไม่เปิดแอพ
        //_showNotification();  // แสดงการแจ้งเตือนเมื่อแอปถูกกดปุ่มhomeหรือปุ่มbackหรือปุ่มหน้าต่างทั้งหมด
      }
    }*/

    if(state == AppLifecycleState.paused){
      i=0; //Reset i value
      _stopWatchTimer.onResetTimer();
      _stopWatchTimer
          .onStartTimer();
        _startResetTimer(0,10);
      //fetchData();
    }
  
    else if (state == AppLifecycleState.resumed){
      i=1; //Set i value
      _stopWatchTimer.onResetTimer();
      _stopWatchTimer
          .onStartTimer();
      if(countfall!=0){
        _startResetTimer(2,0); //กรณีล้มทุก 2 นาทีรีข้อมูล อยู่หน้าแอพ ตอนนี้ยังใช้ไม่ได้
        //fetchData();
      }
      else if(countfall==0){  //กรณีไม่ล้ม
        _startResetTimer(0,10);
        //fetchData();
      }
    }
  }
  

  //Notification function
  Future<void> _showNotification() async {
    const AndroidNotificationDetails androidNotificationDetails =
        AndroidNotificationDetails('nextflow_noti_001', 'Urgent Alert',
            importance: Importance.max,
            priority: Priority.high,
            ticker: 'ticker');

    const NotificationDetails platformChannelDetails = NotificationDetails(
      android: androidNotificationDetails,
    );

    await flutterLocalNotificationsPlugin.show(0, 'Emergency!',
        'Open the app to view the location.', platformChannelDetails);
  }

  //ดึงข้อมูลจาก google sheet
  Future<void> fetchData() async {
    setState(() {
      _isLoading = true;
      //i=0; //Reset i value
    });
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

          if (_latitude != '0' && _longitude != '0' && _latitude != '1' && _longitude != '1') {
            // Navigate to MapsPage after receiving data
            _showNotification(); // Show notification
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

//ดึงข้อมูลจาก http
/*//ตรงข้างในUri.parse ไปเปิด forward path ทุกรอบ กรณีปิด cmd ไปแล้ว ตัวอย่างในดิส
//ตรงข้างในUri.parse ใช้เป็นurlเดิมได้แล้วตอนนี้ (ใช้อันนี้)
  Future<void> fetchData() async {
    setState(() {
      _isLoading = true;
    });
    try {
      final response = await http.get(
        Uri.parse('https://anchovy-just-commonly.ngrok-free.app/'),
      );
      log("this is the response: $response");

      if (response.statusCode == 200) {
        //เชื่อมต่อESP32แบบมีข้อมูลส่งมา
        final jsonResponse = json.decode(response.body);
        _showNotification(); //Show notification
        setState(() {
          _latitude = jsonResponse['message1'];
          _longitude = jsonResponse['message2'];
          _ESP32 = 'ON';
          countfall++;
          _isLoading = false;
        });

        // Navigate to MapsPage after receiving data
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (context) => MapsPage(
              latitude: _latitude,
              longitude: _longitude,
            ),
          ),
        );
      } else {
        //ไม่ได้เชื่อต่อESP32
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
        //เชื่อมต่อESP32แบบไม่มีข้อมูลส่งมา
        _latitude = 'Failed to fetch data';
        _longitude = 'Failed to fetch data';
        _ESP32 = 'ON';
        _isLoading = false;
      });
    }
  }*/

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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        title: Text(widget.title),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: fetchData,
          ),
        ],
      ),
      body: Container(
        padding: const EdgeInsets.all(16.0),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
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
                        child: Text('Share Location'),
                      ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
*/

