using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Documents;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Navigation;
using System.Windows.Shapes;
using System.IO;
using Microsoft.Kinect;
using Microsoft.Kinect.Toolkit.FaceTracking;
using Newtonsoft.Json;

using System.Diagnostics;

namespace SFMocap
{
    /// <summary>
    /// Interaction logic for MainWindow.xaml
    /// </summary>
    public partial class MainWindow : Window
    {
        KinectSensor kinectSensor;
        FaceTracker faceTracker;
        private byte[] colorPixelData;
        private short[] depthPixelData;
        private Skeleton[] skeletonData;

        // Lists to store AU coefficients
        private List<Int64> timeBuffer = new List<Int64>();
        private List<double> lipRaiserBuffer = new List<double>();
        private List<double> jawLowerBuffer = new List<double>();
        private List<double> lipStretchBuffer = new List<double>();
        private List<double> browLowerBuffer = new List<double>();
        private List<double> lipDepressBuffer = new List<double>();
        private List<double> browRaiserBuffer = new List<double>();
        private List<double> xRotation = new List<double>();
        private List<double> yRotation = new List<double>();
        private List<double> zRotation = new List<double>();

        // Boolean for determining when record is enabled or not
        private bool isRecord = false;
        Stopwatch stopwatch = new Stopwatch();

        // Object to record AU for JSON writing
        public class AUCoefficients
        {
            public List<Int64> Time;
            public List<double> LipRaiserAU;
            public List<double> JawLowerAU;
            public List<double> LipStretchAU;
            public List<double> BrowLowerAU;
            public List<double> LipDepressAU;
            public List<double> BrowRaiserAU;
            public List<double> XRotation;
            public List<double> YRotation;
            public List<double> ZRotation;
        }

        public MainWindow()
        {
            InitializeComponent();

            // For a KinectSensor to be detected, we can plug it in after the application has been started.
            KinectSensor.KinectSensors.StatusChanged += KinectSensors_StatusChanged;
            // Or it's already plugged in, so we will look for it.
            var kinect = KinectSensor.KinectSensors.FirstOrDefault(k => k.Status == KinectStatus.Connected);
            if (kinect != null)
            {
                OpenKinect(kinect);
            }
        }

        /// <summary>
        /// Handles the StatusChanged event of the KinectSensors control.
        /// </summary>
        /// <param name="sender">The source of the epent.</param>
        /// <param name="e">The <see cref="Microsoft.Kinect.StatusChangedEventArgs"/> instance containing the event data.</param>
        void KinectSensors_StatusChanged(object sender, StatusChangedEventArgs e)
        {
            if (e.Status == KinectStatus.Connected)
            {
                OpenKinect(e.Sensor);
            }
        }

        /// <summary>
        /// Opens the kinect.
        /// </summary>
        /// <param name="newSensor">The new sensor.</param>
        private void OpenKinect(KinectSensor newSensor)
        {
            kinectSensor = newSensor;

            // Initialize all the necessary streams:
            // - ColorStream with default format
            // - DepthStream with Near mode
            // - SkeletonStream with tracking in NearReange and Seated mode.

            kinectSensor.ColorStream.Enable();

            kinectSensor.DepthStream.Range = DepthRange.Near;
            kinectSensor.DepthStream.Enable(DepthImageFormat.Resolution80x60Fps30);

            kinectSensor.SkeletonStream.EnableTrackingInNearRange = true;
            kinectSensor.SkeletonStream.TrackingMode = SkeletonTrackingMode.Seated;
            kinectSensor.SkeletonStream.Enable(new TransformSmoothParameters() { Correction = 0.5f, JitterRadius = 0.05f, MaxDeviationRadius = 0.05f, Prediction = 0.5f, Smoothing = 0.5f });

            // Listen to the AllFramesReady event to receive KinectSensor's data
            kinectSensor.AllFramesReady += new EventHandler<AllFramesReadyEventArgs>(kinectSensor_AllFramesReady);

            // Initialize data arrays
            colorPixelData = new byte[kinectSensor.ColorStream.FramePixelDataLength];
            depthPixelData = new short[kinectSensor.DepthStream.FramePixelDataLength];
            skeletonData = new Skeleton[6];

            // Starts the Sensor
            kinectSensor.Start();

            // Initialize a new FaceTracker with the KinectSensor
            faceTracker = new FaceTracker(kinectSensor);
        }

        /// <summary>
        /// Handles the AllFramesReady event of the kinectSensor control.
        /// </summary>
        /// <param name="sender">The source of the event.</param>
        /// <param name="e">The <see cref="Microsoft.Kinect.AllFramesReadyEventArgs"/> instance containing the event data.</param>
        void kinectSensor_AllFramesReady(object sender, AllFramesReadyEventArgs e)
        {
            // Retrieve each single frame and copy the data
            using (ColorImageFrame colorImageFrame = e.OpenColorImageFrame())
            {
                if (colorImageFrame == null)
                    return;
                colorImageFrame.CopyPixelDataTo(colorPixelData);
            }

            using (DepthImageFrame depthImageFrame = e.OpenDepthImageFrame())
            {
                if (depthImageFrame == null)
                    return;
                depthImageFrame.CopyPixelDataTo(depthPixelData);
            }

            using (SkeletonFrame skeletonFrame = e.OpenSkeletonFrame())
            {
                if (skeletonFrame == null)
                    return;
                skeletonFrame.CopySkeletonDataTo(skeletonData);
            }

            // Retrieve the first tracked skeleton if any. Otherwise, do nothing.
            var skeleton = skeletonData.FirstOrDefault(s => s.TrackingState == SkeletonTrackingState.Tracked);
            if (skeleton == null)
                return;

            // Make the faceTracker processing the data.
            FaceTrackFrame faceFrame = faceTracker.Track(kinectSensor.ColorStream.Format, colorPixelData,
                                              kinectSensor.DepthStream.Format, depthPixelData,
                                              skeleton);

            // If a face is tracked, then we can use it
            if (faceFrame.TrackSuccessful)
            {
                // Retrieve only the Animation Units coeffs
                var AUCoeff = faceFrame.GetAnimationUnitCoefficients();

                // Records to list buffer if record is enabled
                if (isRecord == true)
                {
                    // Start stopwatch
                    stopwatch.Start();

                    // AU coefficients
                    lipRaiserBuffer.Add(AUCoeff[AnimationUnit.LipRaiser]);
                    jawLowerBuffer.Add(AUCoeff[AnimationUnit.JawLower]);
                    lipStretchBuffer.Add(AUCoeff[AnimationUnit.LipStretcher]);
                    browLowerBuffer.Add(AUCoeff[AnimationUnit.BrowLower]);
                    lipDepressBuffer.Add(AUCoeff[AnimationUnit.LipCornerDepressor]);
                    browRaiserBuffer.Add(AUCoeff[AnimationUnit.BrowLower]);
                    // Face rotation
                    xRotation.Add(faceFrame.Rotation.X);
                    yRotation.Add(faceFrame.Rotation.Y);
                    zRotation.Add(faceFrame.Rotation.Z);
                    // Get time in ms
                    timeBuffer.Add(stopwatch.ElapsedMilliseconds);
                }

                // Display on UI coefficients and rotation for user
                LipRaiser.Content = AUCoeff[AnimationUnit.LipRaiser];
                JawLower.Content = AUCoeff[AnimationUnit.JawLower];
                LipStretch.Content = AUCoeff[AnimationUnit.LipStretcher];
                BrowLower.Content = AUCoeff[AnimationUnit.BrowLower];
                LipDepress.Content = AUCoeff[AnimationUnit.LipCornerDepressor];
                BrowRaiser.Content = AUCoeff[AnimationUnit.BrowRaiser];
                XRotation.Content = faceFrame.Rotation.X;
                YRotation.Content = faceFrame.Rotation.Y;
                ZRotation.Content = faceFrame.Rotation.Z;

                // Animates the drawn face
                var jawLowerer = AUCoeff[AnimationUnit.JawLower];
                jawLowerer = jawLowerer < 0 ? 0 : jawLowerer;
                MouthScaleTransform.ScaleY = jawLowerer * 5 + 0.1;
                MouthScaleTransform.ScaleX = (AUCoeff[AnimationUnit.LipStretcher] + 1);
                LeftBrow.Y = RightBrow.Y = (AUCoeff[AnimationUnit.BrowLower]) * 40;
                RightBrowRotate.Angle = (AUCoeff[AnimationUnit.BrowRaiser] * 20);
                LeftBrowRotate.Angle = -RightBrowRotate.Angle;
                CanvasRotate.Angle = faceFrame.Rotation.Z;
            }
        }

        // Tracks when record button is click and starts recording to JSON
        private void RecordButton_Click(Object sender, RoutedEventArgs e)
        {
            AUCoefficients au = new AUCoefficients();

            // Toggles on record that will start recording AU coefficients to buffer
            if (!isRecord)
            {
                isRecord = true;
            }
            // When record is disabled write stored AUs to JSON object
            else
            {
                isRecord = false;
                stopwatch.Stop();
                JsonSerializer serializer = new JsonSerializer();

                // Record AUs to object for JSON writer to convert
                au.Time = timeBuffer;
                au.LipRaiserAU = lipRaiserBuffer;
                au.JawLowerAU = jawLowerBuffer;
                au.LipStretchAU = lipStretchBuffer;
                au.BrowLowerAU = browLowerBuffer;
                au.LipDepressAU = lipDepressBuffer;
                au.BrowRaiserAU = browRaiserBuffer;
                au.XRotation = xRotation;
                au.YRotation = yRotation;
                au.ZRotation = zRotation;

                // File path settings -- currently json.txt in My Documents folder
                string myDocuments = Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments);
                string path = System.IO.Path.Combine(myDocuments, "json.txt");

                // Writes AUCoefficients
                using (StreamWriter sw = new StreamWriter(path))
                using (JsonWriter jw = new JsonTextWriter(sw))
                {
                    serializer.Serialize(jw, au);
                }
            }
        }
    }
}
