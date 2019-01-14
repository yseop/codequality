
package template;

import static com.sun.net.httpserver.HttpServer.create;
import static java.io.File.listRoots;

import com.sun.net.httpserver.Authenticator;
import com.sun.net.httpserver.Authenticator.Retry;
import com.sun.net.httpserver.BasicAuthenticator;
import com.sun.net.httpserver.HttpServer;

import java.io.BufferedInputStream;
import java.io.File;
import java.io.IOException;

import javax.lang.model.SourceVersion;
import javax.security.auth.AuthPermission;

import org.w3c.dom.xpath.XPathEvaluator;
import org.xml.sax.ErrorHandler;

class Imports {

    String s;

    BasicAuthenticator basicAuthenticator;
    Authenticator Authenticator;
    Retry retry;
    File[] files = listRoots();
    HttpServer httpServer = create();

    File file;
    BufferedInputStream bufferedInputStream;

    AuthPermission authPermission;
    SourceVersion sourceVersion;

    ErrorHandler errorHandler;
    XPathEvaluator xPathEvaluator;

    Imports() throws IOException {}
}