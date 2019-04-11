using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Text;
using System.Threading;
using Xunit;

namespace LibCitisim {

    public class WelcomeService : IDisposable {
        private static WelcomeService instance = null;
        private static readonly object safe = new object();

        private string pwd = Environment.GetEnvironmentVariable("TEST_DIR");
        private string config;
        private Process welcomeServer;

        WelcomeService() {
            Console.WriteLine("++++ called constructor of Welcome Service");
            config = pwd + "/tests.config";

            welcomeServer = new Process();
            welcomeServer.StartInfo.FileName = "citisim-welcome";
            welcomeServer.StartInfo.Arguments = "--Ice.Config=" + config;
            welcomeServer.StartInfo.WorkingDirectory = pwd;
            welcomeServer.StartInfo.UseShellExecute = false;
            welcomeServer.StartInfo.RedirectStandardError = true;
            welcomeServer.StartInfo.RedirectStandardOutput = true;

            StringBuilder output = new StringBuilder();
            EventWaitHandle ev = new EventWaitHandle(false, EventResetMode.AutoReset);
            welcomeServer.OutputDataReceived += new DataReceivedEventHandler((sender, e) => {
                if (!String.IsNullOrEmpty(e.Data)) {
                    output.Append(e.Data);
                    ev.Set();
                }
            });
            welcomeServer.ErrorDataReceived += new DataReceivedEventHandler((sender, e) => {
                if (!String.IsNullOrEmpty(e.Data)) {
                    Console.WriteLine("ERROR:" + e.Data);
                }
            });
            Assert.True(welcomeServer.Start());
            welcomeServer.BeginOutputReadLine();
            welcomeServer.BeginErrorReadLine();

            ev.WaitOne(5000);
            if (welcomeServer.HasExited) {
                Console.WriteLine("ERROR:" + welcomeServer.StandardError.ReadToEnd());
            }
            Assert.Contains("WelcomeServer -t -e 1.1:tcp -h 127.0.0.1", output.ToString());
        }

        public void Dispose() {
            if (welcomeServer == null)
                return;

            Console.WriteLine("---- killing Welcome service...");
            welcomeServer.Kill();
            welcomeServer.WaitForExit(5000);
        }

        public static void StopService() {
            lock (safe) {
                if (instance == null)
                    return;
                instance.Dispose();
            }
        }

        public static void StartService() {
            lock (safe) {
                if (instance != null)
                    return;
                instance = new WelcomeService();
            }
        }
    }
}
