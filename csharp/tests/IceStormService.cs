using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Text;
using System.Threading;
using Xunit;

namespace LibCitisim {

    public class ISService : IDisposable {
        private static ISService instance = null;
        private static readonly object safe = new object();

        private string pwd = Environment.GetEnvironmentVariable("TEST_DIR");
        private string config;
        private Process isServer;

        ISService() {
            Console.WriteLine("++++ called constructor of IS Service");
            config = pwd + "/tests.config";
            var dbPath = "/tmp/test-libcitisim-is-db";

            if (Directory.Exists(dbPath))
                Directory.Delete(dbPath, true);
            Directory.CreateDirectory(dbPath);

            isServer = new Process();
            isServer.StartInfo.FileName = "icebox";
            isServer.StartInfo.Arguments = "--Ice.Config=" + config;
            isServer.StartInfo.WorkingDirectory = pwd;
            isServer.StartInfo.UseShellExecute = false;
            isServer.StartInfo.RedirectStandardError = true;
            isServer.StartInfo.RedirectStandardOutput = true;

            StringBuilder output = new StringBuilder();
            EventWaitHandle ev = new EventWaitHandle(false, EventResetMode.AutoReset);
            isServer.OutputDataReceived += new DataReceivedEventHandler((sender, e) => {
                if (!String.IsNullOrEmpty(e.Data)) {
                    output.Append(e.Data);
                    ev.Set();
                }
            });
            isServer.ErrorDataReceived += new DataReceivedEventHandler((sender, e) => {
                if (!String.IsNullOrEmpty(e.Data)) {
                    Console.WriteLine(e.Data);
                }
            });
            Assert.True(isServer.Start());
            isServer.BeginOutputReadLine();
            isServer.BeginErrorReadLine();

            ev.WaitOne(5000);
            if (isServer.HasExited) {
                Console.WriteLine(isServer.StandardError.ReadToEnd());
            }
            Assert.Equal("IceStorm is ready", output.ToString());
        }

        public void Dispose() {
            if (isServer == null)
                return;

            Console.WriteLine("---- killing IS service...");
            isServer.Kill();
            isServer.WaitForExit(5000);
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
                instance = new ISService();
            }
        }
    }
}
